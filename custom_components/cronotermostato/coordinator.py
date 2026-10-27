"""Manager e logica di schedulazione per Cronotermostato Multizona."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, time, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
import homeassistant.util.dt as dt_util

from .const import (
    CONF_CLIMATE_ENTITIES,
    CONF_RESTORE_ON_STARTUP,
    CONF_SEASON_INVERT,
    CONF_SEASON_SWITCH,
    CONF_SECONDARY_CLIMATE_ENTITIES,
    CONF_SLOTS_COUNT,
    CONF_ZONE_NAME,
    DEFAULT_RESTORE_ON_STARTUP,
    DEFAULT_SEASON_INVERT,
    DEFAULT_SLOTS_COUNT,
    DEFAULT_ZONE_NAME,
    PRESET_COMFORT,
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

        # Configurazione
        self.zone_name: str = entry.data.get(CONF_ZONE_NAME, DEFAULT_ZONE_NAME)
        self.climate_entities: list[str] = entry.data.get(CONF_CLIMATE_ENTITIES, [])
        self.secondary_climate_entities: list[str] = entry.data.get(CONF_SECONDARY_CLIMATE_ENTITIES, [])
        self.season_switch: str | None = entry.data.get(CONF_SEASON_SWITCH)
        self.season_invert: bool = entry.data.get(CONF_SEASON_INVERT, DEFAULT_SEASON_INVERT)
        self.slots_count: int = int(entry.data.get(CONF_SLOTS_COUNT, DEFAULT_SLOTS_COUNT))
        self.restore_on_startup: bool = entry.data.get(CONF_RESTORE_ON_STARTUP, DEFAULT_RESTORE_ON_STARTUP)

        # Switch interni della zona
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

    async def async_setup(self) -> None:
        """Avvia il monitoraggio temporale della zona."""
        # Registra il trigger ogni minuto (secondo 0)
        self._unsub_timer = async_track_time_change(
            self.hass, self._async_minute_tick, second=0
        )

        if self.restore_on_startup:
            # Calcola e applica la fascia corrispondente all'ora attuale
            self.hass.async_create_task(self._async_apply_current_slot(is_startup=True))

    async def async_unload(self) -> None:
        """Ferma i timer e pulisce le risorse."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
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
            return True  # Senza switch stagione, consideriamo modalità invernale completa

        state = self.hass.states.get(self.season_switch)
        if not state or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return True

        is_on = state.state == STATE_ON
        # Se season_invert è False (default come nel package):
        # ON = Inverno, OFF = Estate
        if not self.season_invert:
            return is_on
        # Se invertita: ON = Estate, OFF = Inverno
        return not is_on

    def get_target_climates(self) -> list[str]:
        """Determina quali climate devono essere comandati in base alla stagione e alla zona notte."""
        targets = list(self.climate_entities)

        if self.is_winter():
            # In inverno partecipano sempre tutti
            targets.extend(self.secondary_climate_entities)
        else:
            # In estate, i secondari partecipano solo se abilitato lo switch
            if self.secondary_participates_summer:
                targets.extend(self.secondary_climate_entities)

        return list(dict.fromkeys(targets))  # Elimina duplicati preservando l'ordine

    async def _async_minute_tick(self, now: datetime) -> None:
        """Eseguito ogni minuto: controlla se una fascia oraria scatta in questo minuto."""
        cur_time = now.time()

        for slot_num in range(1, self.slots_count + 1):
            slot = self.slots.get(slot_num)
            if not slot:
                continue

            # Confronto ore e minuti
            if slot.time.hour == cur_time.hour and slot.time.minute == cur_time.minute:
                _LOGGER.debug(
                    "Zona '%s': Scattata fascia oraria %d (%02d:%02d) - Modalità: %s",
                    self.zone_name,
                    slot_num,
                    slot.time.hour,
                    slot.time.minute,
                    slot.preset,
                )
                await self.async_apply_slot(slot_num)
                break

    async def _async_apply_current_slot(self, is_startup: bool = False) -> None:
        """Determina quale fascia è attiva in base all'orario attuale e la applica."""
        now = dt_util.now().time()

        # Trova la fascia più recente la cui ora è <= ora attuale
        best_slot: int | None = None
        best_time: time | None = None

        for slot_num, slot in self.slots.items():
            if slot.preset == PRESET_NONE:
                continue

            if slot.time <= now:
                if best_time is None or slot.time > best_time:
                    best_time = slot.time
                    best_slot = slot_num

        # Se non c'è nessuna fascia precedente oggi, prendiamo l'ultima della giornata di ieri
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
                "%sZona '%s': Applicazione fascia corrente %d (orario %s, preset '%s')",
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
        if not slot:
            return False

        if not self.crono_enabled:
            self.last_action_message = f"Fascia {slot_num} ignorata (Crono disabilitato)"
            _LOGGER.debug("Zona '%s': %s", self.zone_name, self.last_action_message)
            self._notify_listeners()
            return False

        if not self.auto_enabled:
            self.last_action_message = f"Fascia {slot_num} ignorata (Termoregolazione Auto disabilitata)"
            _LOGGER.debug("Zona '%s': %s", self.zone_name, self.last_action_message)
            self._notify_listeners()
            return False

        if slot.preset == PRESET_NONE:
            self.last_action_message = f"Fascia {slot_num} saltata (impostata su NONE)"
            _LOGGER.debug("Zona '%s': %s", self.zone_name, self.last_action_message)
            self._notify_listeners()
            return False

        targets = self.get_target_climates()
        if not targets:
            self.last_action_message = "Nessuna entità climate configurata"
            _LOGGER.warning("Zona '%s': %s", self.zone_name, self.last_action_message)
            self._notify_listeners()
            return False

        try:
            _LOGGER.info(
                "Zona '%s': Applicazione preset '%s' su %s (Stagione: %s)",
                self.zone_name,
                slot.preset,
                targets,
                "Inverno" if self.is_winter() else "Estate",
            )
            await self.hass.services.async_call(
                "climate",
                "set_preset_mode",
                {
                    "entity_id": targets,
                    "preset_mode": slot.preset,
                },
                blocking=True,
            )
            self.active_slot = slot_num
            self.last_applied_time = dt_util.now()
            self.last_applied_preset = slot.preset
            self.last_action_message = (
                f"Fascia {slot_num} ({slot.preset}) applicata con successo alle {dt_util.now().strftime('%H:%M:%S')}"
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

        # Se sono tutte passate per oggi, la prima di domani
        first = sorted_slots[0]
        return first.index, first.time, first.preset
