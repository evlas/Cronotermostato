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
    CONF_SCENE_SENSOR,
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
    MODE_SCENE,
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
    time(12, 0),
    time(18, 0),
    time(22, 30),
]


class SlotData:
    """Rappresenta una fascia oraria programmata."""

    def __init__(self, index: int, slot_time: time, preset: str) -> None:
        """Inizializza la fascia."""
        self.index = index
        self.time = slot_time
        self.preset = preset


class CronotermostatoZoneManager:
    """Gestisce la logica di controllo, le fasce orarie e le scene per una zona."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Inizializza il manager della zona."""
        self.hass = hass
        self.entry = entry

        # Configurazione base
        self.zone_name: str = entry.data.get(CONF_ZONE_NAME, DEFAULT_ZONE_NAME)
        self.climate_entities: list[str] = entry.data.get(CONF_CLIMATE_ENTITIES, [])
        self.secondary_climate_entities: list[str] = entry.data.get(CONF_SECONDARY_CLIMATE_ENTITIES, [])
        self.season_switch: str | None = entry.data.get(CONF_SEASON_SWITCH)
        self.season_invert: bool = entry.data.get(CONF_SEASON_INVERT, DEFAULT_SEASON_INVERT)
        self.slots_count: int = int(entry.data.get(CONF_SLOTS_COUNT, DEFAULT_SLOTS_COUNT))
        self.restore_on_startup: bool = entry.data.get(CONF_RESTORE_ON_STARTUP, DEFAULT_RESTORE_ON_STARTUP)
        self.off_preset: str = entry.data.get(CONF_OFF_PRESET, DEFAULT_OFF_PRESET)

        # Configurazione sensore Scena / Presenza unificato
        self.scene_sensor: str | None = entry.data.get(
            CONF_SCENE_SENSOR, entry.data.get(CONF_KNX_SCENE_SENSOR)
        )

        # Sensori KNX specifici (mantenuti per compatibilità se configurati in precedenza)
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
        self._unsub_scenes: CALLBACK_TYPE | None = None

    async def async_setup(self) -> None:
        """Avvia il monitoraggio temporale e delle scene della zona."""
        # 1. Registra il trigger ogni minuto
        self._unsub_timer = async_track_time_change(
            self.hass, self._async_minute_tick, second=0
        )

        # 2. Registra listener per il sensore Scene / Presenza
        tracked_entities: list[str] = []
        for entity in [
            self.scene_sensor,
            self.knx_scene_in_casa,
            self.knx_scene_uscita,
            self.knx_scene_notte,
            self.knx_scene_vacanza,
        ]:
            if entity and entity not in tracked_entities:
                tracked_entities.append(entity)

        if tracked_entities:
            self._unsub_scenes = async_track_state_change_event(
                self.hass, tracked_entities, self._async_scene_changed
            )
            _LOGGER.debug(
                "Zona '%s': Monitoraggio Scene attivo su: %s",
                self.zone_name,
                tracked_entities,
            )

        # 3. Allineamento all'avvio
        if self.restore_on_startup:
            self.hass.async_create_task(self._async_apply_current_slot(is_startup=True))

    async def async_unload(self) -> None:
        """Ferma i timer e pulisce le risorse."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
        if self._unsub_scenes:
            self._unsub_scenes()
            self._unsub_scenes = None
        self._listeners.clear()

    @callback
    def async_add_listener(self, update_callback: Callable[[], None]) -> CALLBACK_TYPE:
        """Aggiunge un listener per gli aggiornamenti dello stato."""
        self._listeners.append(update_callback)

        def _remove_listener() -> None:
            self._listeners.remove(update_callback)

        return _remove_listener

    def _notify_listeners(self) -> None:
        """Notifica tutti i listener registrati."""
        for callback_fn in self._listeners:
            callback_fn()

    def is_winter(self) -> bool:
        """Determina la stagione corrente: True se Inverno, False se Estate."""
        if not self.season_switch:
            return True

        state = self.hass.states.get(self.season_switch)
        if not state:
            return True

        is_on = state.state == STATE_ON
        return not is_on if self.season_invert else is_on

    def get_target_climates(self) -> list[str]:
        """Restituisce le entità climate attive per la stagione corrente."""
        targets = list(self.climate_entities)

        if self.is_winter():
            targets.extend(self.secondary_climate_entities)
        else:
            if self.secondary_participates_summer:
                targets.extend(self.secondary_climate_entities)

        return list(dict.fromkeys(targets))

    async def async_set_crono_enabled(self, enabled: bool) -> None:
        """Abilita o disabilita il cronotermostato per la zona."""
        self.crono_enabled = enabled
        if enabled:
            self.mode = MODE_CRONOTERMOSTATO
            await self._async_apply_current_slot()
        else:
            if self.mode == MODE_CRONOTERMOSTATO:
                self.mode = MODE_OFF
                await self.async_apply_preset(self.off_preset, "Cronotermostato disattivato (OFF)")
        self._notify_listeners()

    async def async_set_auto_enabled(self, enabled: bool) -> None:
        """Abilita o disabilita la modalità automatica."""
        self.auto_enabled = enabled
        if enabled:
            if self.mode == MODE_OFF:
                self.mode = MODE_CRONOTERMOSTATO
                await self._async_apply_current_slot()
            elif self.mode == MODE_SCENE:
                await self._async_check_and_apply_current_scene()
        else:
            self.mode = MODE_MANUALE
            self.last_action_message = "Modalità Manuale attivata"
        self._notify_listeners()

    async def async_set_secondary_participates_summer(self, participates: bool) -> None:
        """Imposta se la zona secondaria (es. zona notte) partecipa al raffrescamento estivo."""
        self.secondary_participates_summer = participates
        _LOGGER.info(
            "Zona '%s': Partecipazione zona secondaria in estate impostata a %s",
            self.zone_name,
            participates,
        )
        if not self.is_winter():
            await self._async_reapply_active_state("Aggiornamento partecipazione estiva")
        self._notify_listeners()

    async def async_set_mode(self, mode: str) -> None:
        """Cambia la modalità operativa globale della zona."""
        # Supporto retrocompatibile se mode arriva come 'scene_knx'
        if mode == "scene_knx":
            mode = MODE_SCENE

        self.mode = mode

        if mode == MODE_CRONOTERMOSTATO:
            self.crono_enabled = True
            self.auto_enabled = True
            await self._async_apply_current_slot()

        elif mode == MODE_SCENE:
            self.crono_enabled = False
            self.auto_enabled = True
            self.active_slot = None
            # Valuta lo stato attuale della scena
            await self._async_check_and_apply_current_scene()

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

    async def _async_scene_changed(self, event: Event[EventStateChangedData]) -> None:
        """Gestisce il cambio stato del sensore Scena / Presenza."""
        if self.mode != MODE_SCENE and self.crono_enabled:
            return
        if not self.auto_enabled:
            return

        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")
        if not new_state or new_state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return

        state_val = str(new_state.state).strip()
        await self._process_scene_state(entity_id, state_val)

    async def _process_scene_state(self, entity_id: str, state_val: str) -> None:
        """Applica il preset corrispondente alla scena rilevata."""
        preset_to_apply: str | None = None
        source_scene = ""
        st_lower = state_val.lower().strip()

        # 1. Matching sensore scena unificato (es. sensor.ultima_scena)
        if entity_id in (self.scene_sensor, self.knx_scene_sensor):
            if st_lower in ("in casa", "in_casa", "home", "comfort"):
                preset_to_apply = PRESET_COMFORT
                source_scene = f"Scena '{state_val}' (Comfort)"
            elif st_lower in ("uscita", "away", "eco"):
                preset_to_apply = PRESET_AWAY
                source_scene = f"Scena '{state_val}' (Away)"
            elif st_lower in ("notte", "night", "sleep", "economy"):
                preset_to_apply = PRESET_ECONOMY
                source_scene = f"Scena '{state_val}' (Economy)"
            elif st_lower in ("vacanza", "holiday", "protezione"):
                preset_to_apply = PRESET_BUILDING_PROTECTION
                source_scene = f"Scena '{state_val}' (Building Protection)"

        # 2. Supporto retrocompatibile sensori KNX singoli se ancora configurati
        elif entity_id == self.knx_scene_in_casa and state_val == "3":
            preset_to_apply = PRESET_COMFORT
            source_scene = "Scena In Casa (3)"
        elif entity_id == self.knx_scene_uscita and state_val == "2":
            preset_to_apply = PRESET_AWAY
            source_scene = "Scena Uscita (2)"
        elif entity_id == self.knx_scene_notte and state_val == "4":
            preset_to_apply = PRESET_ECONOMY
            source_scene = "Scena Notte (4)"
        elif entity_id == self.knx_scene_vacanza and state_val == "5":
            preset_to_apply = PRESET_BUILDING_PROTECTION
            source_scene = "Scena Vacanza (5)"

        if preset_to_apply:
            self.active_slot = None
            await self.async_apply_preset(preset_to_apply, source_scene)

    async def _async_check_and_apply_current_scene(self) -> None:
        """Controlla lo stato attuale all'ingresso in modalità Scena."""
        # 1. Controlla prima il sensore unificato
        if self.scene_sensor:
            st = self.hass.states.get(self.scene_sensor)
            if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                await self._process_scene_state(self.scene_sensor, st.state)
                return

        # 2. Fallback sui sensori individuali KNX se presenti
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
                    await self._process_scene_state(ent, st.state)
                    return

        # Fallback default se nessuna scena attiva
        await self.async_apply_preset(PRESET_COMFORT, "Passaggio a Scena (Default Comfort)")

    async def _async_apply_current_slot(self, is_startup: bool = False) -> None:
        """Determina quale fascia è attiva in base all'orario attuale e la applica."""
        if not self.crono_enabled or not self.auto_enabled or self.mode != MODE_CRONOTERMOSTATO:
            return

        now = dt_util.now().time()
        best_slot: int | None = None
        best_time: time | None = None

        for slot_num, slot in self.slots.items():
            if not slot.preset or slot.preset.lower() in (PRESET_NONE, "none"):
                continue

            if slot.time <= now:
                if best_time is None or slot.time > best_time:
                    best_time = slot.time
                    best_slot = slot_num

        if best_slot is None:
            max_time: time | None = None
            for slot_num, slot in self.slots.items():
                if not slot.preset or slot.preset.lower() in (PRESET_NONE, "none"):
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
        if not slot or not slot.preset or slot.preset.lower() in (PRESET_NONE, "none"):
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
            _LOGGER.error("Zona '%s': Errore chiamata climate.set_preset_mode: %s", self.zone_name, err)
            self._notify_listeners()
            return False

    async def _async_reapply_active_state(self, reason: str) -> None:
        """Riapplica lo stato attivo (fascia corrente o scena)."""
        if self.mode == MODE_CRONOTERMOSTATO and self.crono_enabled:
            await self._async_apply_current_slot()
        elif self.mode == MODE_SCENE:
            await self._async_check_and_apply_current_scene()
        elif self.mode == MODE_OFF:
            await self.async_apply_preset(self.off_preset, reason)

    def get_next_slot_info(self) -> tuple[int | None, time | None, str | None]:
        """Restituisce informazioni sulla prossima fascia oraria programmata."""
        if self.mode != MODE_CRONOTERMOSTATO or not self.crono_enabled:
            return None, None, None

        now = dt_util.now().time()
        sorted_slots = sorted(
            [s for s in self.slots.values() if s.preset and s.preset.lower() not in (PRESET_NONE, "none")],
            key=lambda s: s.time,
        )

        if not sorted_slots:
            return None, None, None

        for s in sorted_slots:
            if s.time > now:
                return s.index, s.time, s.preset

        first = sorted_slots[0]
        return first.index, first.time, first.preset
