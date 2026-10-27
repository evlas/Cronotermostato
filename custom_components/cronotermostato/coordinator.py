"""Manager e logica di schedulazione per Cronotermostato Multizona."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, time, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
import homeassistant.util.dt as dt_util

from .const import (
    CONF_CLIMATE_ENTITIES,
    CONF_KNX_SCENE_IN_CASA,
    CONF_KNX_SCENE_NOTTE,
    CONF_KNX_SCENE_SENSOR,
    CONF_KNX_SCENE_USCITA,
    CONF_KNX_SCENE_VACANZA,
    CONF_OFF_PRESET,
    CONF_RESTORE_ON_STARTUP,
    CONF_SEASON_INVERT,
    CONF_SEASON_SWITCH,
    CONF_SECONDARY_CLIMATE_ENTITIES,
    CONF_SLOTS_COUNT,
    CONF_ZONE_NAME,
    DEFAULT_OFF_PRESET,
    DEFAULT_RESTORE_ON_STARTUP,
    DEFAULT_SEASON_INVERT,
    DEFAULT_SLOTS_COUNT,
    DEFAULT_ZONE_NAME,
    MODE_CRONOTERMOSTATO,
    MODE_MANUALE,
    MODE_OFF,
    MODE_SCENE_KNX,
    PRESET_AWAY,
    PRESET_BUILDING_PROTECTION,
    PRESET_COMFORT,
    PRESET_ECONOMY,
    PRESET_NONE,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_SLOT_TIMES = [
    time(6, 30),
    time(8, 30),
    time(12, 30),
    time(18, 0),
    time(22, 30),
    time(0, 0),
    time(0, 0),
    time(0, 0),
    time(0, 0),
    time(0, 0),
]


class SlotData:
    """Rappresenta una fascia oraria programmata."""

    def __init__(self, index: int, slot_time: time, preset: str = PRESET_COMFORT) -> None:
        self.index = index
        self.time = slot_time
        self.preset = preset


class CronotermostatoZoneManager:
    """Gestisce la logica di una zona del cronotermostato."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Inizializza il manager per la zona."""
        self.hass = hass
        self.entry = entry

        # Configurazione principale
        self.zone_name: str = entry.data.get(CONF_ZONE_NAME, DEFAULT_ZONE_NAME)
        self.climate_entities: list[str] = entry.data.get(CONF_CLIMATE_ENTITIES, [])
        self.secondary_climate_entities: list[str] = entry.data.get(CONF_SECONDARY_CLIMATE_ENTITIES, [])
        self.season_switch: str | None = entry.data.get(CONF_SEASON_SWITCH)
        self.season_invert: bool = entry.data.get(CONF_SEASON_INVERT, DEFAULT_SEASON_INVERT)
        self.slots_count: int = int(entry.data.get(CONF_SLOTS_COUNT, DEFAULT_SLOTS_COUNT))
        self.restore_on_startup: bool = entry.data.get(CONF_RESTORE_ON_STARTUP, DEFAULT_RESTORE_ON_STARTUP)
        self.off_preset: str = entry.data.get(CONF_OFF_PRESET, DEFAULT_OFF_PRESET)

        # Configurazione sensori Scene KNX
        self.knx_scene_sensor: str | None = entry.data.get(CONF_KNX_SCENE_SENSOR)
        self.knx_scene_in_casa: str | None = entry.data.get(CONF_KNX_SCENE_IN_CASA)
        self.knx_scene_uscita: str | None = entry.data.get(CONF_KNX_SCENE_USCITA)
        self.knx_scene_notte: str | None = entry.data.get(CONF_KNX_SCENE_NOTTE)
        self.knx_scene_vacanza: str | None = entry.data.get(CONF_KNX_SCENE_VACANZA)

        # Modalità operativa di zona
        self.mode: str = MODE_CRONOTERMOSTATO
        self.crono_enabled: bool = True
        self.auto_enabled: bool = True
        self.secondary_participates_summer: bool = True

        # Fasce orarie
        self.slots: dict[int, SlotData] = {}
        for i in range(1, self.slots_count + 1):
            default_t = DEFAULT_SLOT_TIMES[i - 1] if i - 1 < len(DEFAULT_SLOT_TIMES) else time(0, 0)
            self.slots[i] = SlotData(i, default_t, PRESET_COMFORT)

        # Stato corrente
        self.active_slot: int | None = None
        self.last_applied_time: datetime | None = None
        self.last_applied_preset: str | None = None
        self.last_action_message: str = "In attesa del primo avvio"

        self._listeners: list[Callable[[], None]] = []
        self._unsub_timer: CALLBACK_TYPE | None = None
        self._unsub_knx_scenes: CALLBACK_TYPE | None = None

    async def async_setup(self) -> None:
        """Avvia il monitoraggio temporale e delle scene KNX della zona."""
        # 1. Registra il trigger ogni minuto
        self._unsub_timer = async_track_time_change(
            self.hass, self._async_minute_tick, second=0
        )

        # 2. Registra listener per sensori Scene KNX
        knx_entities: list[str] = []
        for entity in [
            self.knx_scene_sensor,
            self.knx_scene_in_casa,
            self.knx_scene_uscita,
            self.knx_scene_notte,
            self.knx_scene_vacanza,
        ]:
            if entity and entity not in knx_entities:
                knx_entities.append(entity)

        if knx_entities:
            self._unsub_knx_scenes = async_track_state_change_event(
                self.hass, knx_entities, self._async_knx_scene_changed
            )
            _LOGGER.debug(
                "Zona '%s': Monitoraggio Scene KNX attivo su: %s",
                self.zone_name,
                knx_entities,
            )

        # 3. Allineamento all'avvio
        if self.restore_on_startup:
            self.hass.async_create_task(self._async_apply_current_slot(is_startup=True))

    async def async_unload(self) -> None:
        """Ferma i timer e pulisce le risorse."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
        if self._unsub_knx_scenes:
            self._unsub_knx_scenes()
            self._unsub_knx_scenes = None
        self._listeners.clear()

    @callback
    def async_add_listener(self, update_callback: Callable[[], None]) -> CALLBACK_TYPE:
        """Aggiunge un listener per gli aggiornamenti dello stato."""
        self._listeners.append(update_callback)

        @callback
        def remove_listener() -> None:
            if update_callback in self._listeners:
                self._listeners.remove(update_callback)

        return remove_listener

    @callback
    def _notify_listeners(self) -> None:
        """Notifica tutte le entità collegate che lo stato è cambiato."""
        for listener in self._listeners:
            listener()

    def is_winter(self) -> bool:
        """Verifica se la stagione corrente è Inverno."""
        if not self.season_switch:
            return True

        state = self.hass.states.get(self.season_switch)
        if not state or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return True

        is_on = state.state == STATE_ON
        if not self.season_invert:
            return is_on
        return not is_on

    def get_target_climates(self) -> list[str]:
        """Determina quali climate devono essere comandati in base alla stagione e alla zona notte."""
        targets = list(self.climate_entities)
        if self.is_winter():
            targets.extend(self.secondary_climate_entities)
        else:
            if self.secondary_participates_summer:
                targets.extend(self.secondary_climate_entities)

        return list(dict.fromkeys(targets))

    async def async_set_mode(self, mode: str) -> None:
        """Cambia la modalità operativa globale della zona (Cronotermostato, Scene KNX, Manuale, Off)."""
        _LOGGER.info("Zona '%s': Cambio modalità da '%s' a '%s'", self.zone_name, self.mode, mode)
        self.mode = mode

        if mode == MODE_CRONOTERMOSTATO:
            self.crono_enabled = True
            self.auto_enabled = True
            await self._async_apply_current_slot()

        elif mode == MODE_SCENE_KNX:
            self.crono_enabled = False
            self.auto_enabled = True
            self.active_slot = None
            # Valuta lo stato attuale delle scene KNX
            await self._async_check_and_apply_current_knx_scene()

        elif mode == MODE_OFF:
            self.crono_enabled = False
            self.auto_enabled = False
            self.active_slot = None
            await self.async_apply_preset(self.off_preset, "Zona Disattivata (OFF)")

        elif mode == MODE_MANUALE:
            self.crono_enabled = False
            self.auto_enabled = False
            self.active_slot = None
            self.last_action_message = "Modalità Manuale attiva (Schedulazione sospesa)"

        self._notify_listeners()

    async def _async_minute_tick(self, now: datetime) -> None:
        """Eseguito ogni minuto: controlla le fasce se siamo in modalità Cronotermostato."""
        if self.mode != MODE_CRONOTERMOSTATO or not self.crono_enabled or not self.auto_enabled:
            return

        cur_time = now.time()
        for slot_num in range(1, self.slots_count + 1):
            slot = self.slots.get(slot_num)
            if not slot:
                continue

            if slot.time.hour == cur_time.hour and slot.time.minute == cur_time.minute:
                _LOGGER.debug(
                    "Zona '%s': Scattata fascia oraria %d (%02d:%02d) - Preset: %s",
                    self.zone_name,
                    slot_num,
                    slot.time.hour,
                    slot.time.minute,
                    slot.preset,
                )
                await self.async_apply_slot(slot_num)
                break

    async def _async_knx_scene_changed(self, event: Event[EventStateChangedData]) -> None:
        """Gestisce il cambio stato dei sensori Scene KNX."""
        # Se la modalità è Cronotermostato o Spento, le scene KNX vengono ignorate
        if self.mode not in (MODE_SCENE_KNX, MODE_MANUALE) and self.crono_enabled:
            return
        if not self.auto_enabled:
            return

        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")
        if not new_state or new_state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return

        state_val = str(new_state.state).strip()
        await self._process_knx_scene_state(entity_id, state_val)

    async def _process_knx_scene_state(self, entity_id: str, state_val: str) -> None:
        """Applica il preset corrispondente alla scena KNX rilevata."""
        preset_to_apply: str | None = None
        source_scene = ""

        # Controllo sensori individuali tipici della configurazione di Vito
        if entity_id == self.knx_scene_in_casa and state_val == "3":
            preset_to_apply = PRESET_COMFORT
            source_scene = "Scena KNX In Casa (3)"
        elif entity_id == self.knx_scene_uscita and state_val == "2":
            preset_to_apply = PRESET_AWAY
            source_scene = "Scena KNX Uscita (2)"
        elif entity_id == self.knx_scene_notte and state_val == "4":
            preset_to_apply = PRESET_ECONOMY
            source_scene = "Scena KNX Notte (4)"
        elif entity_id == self.knx_scene_vacanza and state_val == "5":
            preset_to_apply = PRESET_BUILDING_PROTECTION
            source_scene = "Scena KNX Vacanza (5)"
        elif entity_id == self.knx_scene_sensor:
            # Sensore unificato di scena DPT 17.001 o 18.001
            if state_val in ("3", "in_casa", "home", "comfort"):
                preset_to_apply = PRESET_COMFORT
                source_scene = f"Scena KNX ({state_val} -> comfort)"
            elif state_val in ("2", "uscita", "away"):
                preset_to_apply = PRESET_AWAY
                source_scene = f"Scena KNX ({state_val} -> away)"
            elif state_val in ("4", "notte", "night", "economy"):
                preset_to_apply = PRESET_ECONOMY
                source_scene = f"Scena KNX ({state_val} -> economy)"
            elif state_val in ("5", "vacanza", "holiday", "protection"):
                preset_to_apply = PRESET_BUILDING_PROTECTION
                source_scene = f"Scena KNX ({state_val} -> building_protection)"

        if preset_to_apply:
            self.active_slot = None
            await self.async_apply_preset(preset_to_apply, source_scene)

    async def _async_check_and_apply_current_knx_scene(self) -> None:
        """Controlla lo stato attuale dei sensori KNX all'ingresso in modalità Scene KNX."""
        # Controlla prima vacanza, poi notte, poi uscita, poi in casa
        pairs = [
            (self.knx_scene_vacanza, "5"),
            (self.knx_scene_notte, "4"),
            (self.knx_scene_uscita, "2"),
            (self.knx_scene_in_casa, "3"),
        ]
        for ent, expected in pairs:
            if ent:
                st = self.hass.states.get(ent)
                if st and st.state == expected:
                    await self._process_knx_scene_state(ent, st.state)
                    return

        # Default fallback se nessuna scena attiva
        await self.async_apply_preset(PRESET_COMFORT, "Passaggio a Scene KNX (Default Comfort)")

    async def _async_apply_current_slot(self, is_startup: bool = False) -> None:
        """Determina quale fascia è attiva in base all'orario attuale e la applica."""
        if not self.crono_enabled or not self.auto_enabled or self.mode != MODE_CRONOTERMOSTATO:
            return

        now = dt_util.now().time()
        best_slot: int | None = None
        best_time: time | None = None

        for slot_num, slot in self.slots.items():
            if slot.preset == PRESET_NONE:
                continue

            if slot.time <= now:
                if best_time is None or slot.time > best_time:
                    best_time = slot.time
                    best_slot = slot_num

        if best_slot is None:
            max_time: time | None = None
            for slot_num, slot in self.slots.items():
                if slot.preset == PRESET_NONE:
                    continue
                if max_time is None or slot.time > max_time:
                    max_time = slot.time
                    best_slot = slot_num

        if best_slot is not None:
            prefix = "Avvio Home Assistant: " if is_startup else ""
            _LOGGER.info(
                "%sZona '%s': Applicazione fascia oraria corrente %d (%s, preset '%s')",
                prefix,
                self.zone_name,
                best_slot,
                self.slots[best_slot].time.strftime("%H:%M"),
                self.slots[best_slot].preset,
            )
            await self.async_apply_slot(best_slot)

    async def async_apply_slot(self, slot_num: int) -> bool:
        """Applica la modalità di una fascia oraria specifica ai climate della zona."""
        slot = self.slots.get(slot_num)
        if not slot or slot.preset == PRESET_NONE:
            return False

        success = await self.async_apply_preset(
            slot.preset, f"Fascia {slot_num} ({slot.time.strftime('%H:%M')})"
        )
        if success:
            self.active_slot = slot_num
            self._notify_listeners()
        return success

    async def async_apply_preset(self, preset: str, reason: str) -> bool:
        """Invia un preset ai termostati della zona e aggiorna la diagnostica."""
        targets = self.get_target_climates()
        if not targets:
            self.last_action_message = "Nessun termostato configurato"
            _LOGGER.warning("Zona '%s': %s", self.zone_name, self.last_action_message)
            self._notify_listeners()
            return False

        try:
            _LOGGER.info(
                "Zona '%s': Impostazione preset '%s' su %s per '%s' (Stagione: %s)",
                self.zone_name,
                preset,
                targets,
                reason,
                "Inverno" if self.is_winter() else "Estate",
            )
            await self.hass.services.async_call(
                "climate",
                "set_preset_mode",
                {
                    "entity_id": targets,
                    "preset_mode": preset,
                },
                blocking=True,
            )
            self.last_applied_time = dt_util.now()
            self.last_applied_preset = preset
            self.last_action_message = (
                f"{reason}: impostato '{preset}' alle {dt_util.now().strftime('%H:%M:%S')}"
            )
            self._notify_listeners()
            return True
        except Exception as err:
            self.last_action_message = f"Errore impostazione preset: {err}"
            _LOGGER.error("Zona '%s': Errore chiamata climate.set_preset_mode: %v", self.zone_name, err)
            self._notify_listeners()
            return False

    def get_next_slot_info(self) -> tuple[int | None, time | None, str | None]:
        """Restituisce informazioni sulla prossima fascia oraria programmata."""
        if self.mode != MODE_CRONOTERMOSTATO or not self.crono_enabled:
            return None, None, None

        now = dt_util.now().time()
        sorted_slots = sorted(
            [s for s in self.slots.values() if s.preset != PRESET_NONE],
            key=lambda s: s.time,
        )

        if not sorted_slots:
            return None, None, None

        for s in sorted_slots:
            if s.time > now:
                return s.index, s.time, s.preset

        first = sorted_slots[0]
        return first.index, first.time, first.preset
