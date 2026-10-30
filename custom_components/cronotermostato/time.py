"""Piattaforma Time per la selezione degli orari delle fasce del Cronotermostato."""

from __future__ import annotations

from datetime import time
import logging

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, MODE_CRONOTERMOSTATO
from .coordinator import CronotermostatoZoneManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura le entità Time per ciascuna fascia oraria della zona."""
    manager: CronotermostatoZoneManager = hass.data[DOMAIN][entry.entry_id]

    entities = [
        CronotermostatoSlotTimeEntity(manager, entry, slot_index)
        for slot_index in range(1, manager.slots_count + 1)
    ]

    async_add_entities(entities)


class CronotermostatoSlotTimeEntity(RestoreEntity, TimeEntity):
    """Rappresenta l'orario di avvio di una specifica fascia oraria."""

    _attr_has_entity_name = True

    def __init__(
        self,
        manager: CronotermostatoZoneManager,
        entry: ConfigEntry,
        slot_index: int,
    ) -> None:
        """Inizializza l'entità Time della fascia."""
        self.manager = manager
        self.entry = entry
        self.slot_index = slot_index
        self._attr_translation_key = f"slot_time_{slot_index}"
        self._attr_unique_id = f"{entry.entry_id}_time_slot_{slot_index}"
        self._attr_icon = "mdi:clock-outline"
        self._attr_device_info = manager.device_info

    @property
    def native_value(self) -> time:
        """Restituisce l'orario impostato per la fascia."""
        slot = self.manager.slots.get(self.slot_index)
        if slot:
            return slot.time
        return time(0, 0)

    async def async_set_value(self, value: time) -> None:
        """Modifica l'orario della fascia e ricalcola la fascia attiva."""
        slot = self.manager.slots.get(self.slot_index)
        if slot:
            slot.time = value
            if self.manager.mode == MODE_CRONOTERMOSTATO and self.manager.crono_enabled:
                await self.manager._async_apply_current_slot()
            self.manager._notify_listeners()
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Ripristina lo stato memorizzato all'avvio."""
        await super().async_added_to_hass()
        self.async_on_remove(self.manager.async_add_listener(self.async_write_ha_state))

        last_state = await self.async_get_last_state()
        if last_state and last_state.state:
            try:
                parts = [int(p) for p in last_state.state.split(":")]
                if len(parts) >= 2:
                    restored_time = time(parts[0], parts[1], parts[2] if len(parts) > 2 else 0)
                    slot = self.manager.slots.get(self.slot_index)
                    if slot:
                        slot.time = restored_time
            except Exception as err:
                _LOGGER.debug("Impossibile ripristinare orario per fascia %d: %s", self.slot_index, err)
