"""Piattaforma Select per la scelta dei preset/modalità delle fasce e della modalità operativa."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DEFAULT_PRESET_OPTIONS, DOMAIN, PRESET_COMFORT, ZONE_MODES
from .coordinator import CronotermostatoZoneManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura le entità Select per la modalità operativa e ciascuna fascia oraria della zona."""
    manager: CronotermostatoZoneManager = hass.data[DOMAIN][entry.entry_id]

    entities: list[SelectEntity] = [
        CronotermostatoZoneModeSelect(manager, entry),
    ]

    entities.extend(
        [
            CronotermostatoSlotPresetEntity(manager, entry, slot_index)
            for slot_index in range(1, manager.slots_count + 1)
        ]
    )

    async_add_entities(entities)


class CronotermostatoZoneModeSelect(RestoreEntity, SelectEntity):
    """Rappresenta la modalità operativa globale della zona (Cronotermostato, Scene KNX, Manuale, Off)."""

    _attr_has_entity_name = True
    _attr_translation_key = "zone_mode"
    _attr_icon = "mdi:thermostat-cog"

    def __init__(
        self,
        manager: CronotermostatoZoneManager,
        entry: ConfigEntry,
    ) -> None:
        self.manager = manager
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_select_zone_mode"
        self._attr_options = ZONE_MODES
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Cronotermostato {manager.zone_name}",
            manufacturer="evlas",
            model="Cronotermostato Multizona",
            sw_version="1.0.0",
        )

    @property
    def current_option(self) -> str:
        """Restituisce la modalità attualmente attiva per la zona."""
        return self.manager.mode

    async def async_select_option(self, option: str) -> None:
        """Imposta una nuova modalità operativa per la zona."""
        if option in self._attr_options:
            await self.manager.async_set_mode(option)

    async def async_added_to_hass(self) -> None:
        """Ripristina lo stato memorizzato all'avvio."""
        await super().async_added_to_hass()
        self.async_on_remove(self.manager.async_add_listener(self.async_write_ha_state))

        last_state = await self.async_get_last_state()
        if last_state and last_state.state in self._attr_options:
            await self.manager.async_set_mode(last_state.state)


class CronotermostatoSlotPresetEntity(RestoreEntity, SelectEntity):
    """Rappresenta la modalità o preset assegnato a una specifica fascia oraria."""

    _attr_has_entity_name = True

    def __init__(
        self,
        manager: CronotermostatoZoneManager,
        entry: ConfigEntry,
        slot_index: int,
    ) -> None:
        """Inizializza l'entità Select della fascia."""
        self.manager = manager
        self.entry = entry
        self.slot_index = slot_index
        self._attr_translation_key = f"slot_preset_{slot_index}"
        self._attr_unique_id = f"{entry.entry_id}_select_preset_{slot_index}"
        self._attr_icon = "mdi:tune-vertical"
        self._attr_options = DEFAULT_PRESET_OPTIONS
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Cronotermostato {manager.zone_name}",
            manufacturer="evlas",
            model="Cronotermostato Multizona",
            sw_version="1.0.0",
        )

    @property
    def options(self) -> list[str]:
        """Restituisce le modalità preset supportate dai termostati della zona."""
        return self.manager.get_supported_preset_modes()

    @property
    def current_option(self) -> str:
        """Restituisce la modalità attualmente selezionata per la fascia."""
        slot = self.manager.slots.get(self.slot_index)
        if slot and slot.preset:
            val = slot.preset.lower()
            if val in self.options:
                return val
        return self.options[0] if self.options else PRESET_COMFORT

    async def async_select_option(self, option: str) -> None:
        """Imposta una nuova modalità per la fascia."""
        slot = self.manager.slots.get(self.slot_index)
        if slot and option in self.options:
            slot.preset = option.lower()
            self.manager._notify_listeners()
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Ripristina lo stato memorizzato all'avvio."""
        await super().async_added_to_hass()
        self.async_on_remove(self.manager.async_add_listener(self.async_write_ha_state))

        last_state = await self.async_get_last_state()
        if last_state and last_state.state:
            val = last_state.state.lower()
            if val in self.options or val in DEFAULT_PRESET_OPTIONS:
                slot = self.manager.slots.get(self.slot_index)
                if slot:
                    slot.preset = val
