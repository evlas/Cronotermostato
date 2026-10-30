"""Piattaforma Button per forzare comandi del Cronotermostato."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import CronotermostatoZoneManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura i pulsanti di comando per la zona."""
    manager: CronotermostatoZoneManager = hass.data[DOMAIN][entry.entry_id]

    buttons = [
        CronotermostatoApplyButton(manager, entry),
    ]

    async_add_entities(buttons)


class CronotermostatoApplyButton(ButtonEntity):
    """Pulsante per forzare l'applicazione immediata della fascia oraria corrente."""

    _attr_has_entity_name = True
    _attr_translation_key = "apply_now"
    _attr_icon = "mdi:play-circle-outline"

    def __init__(self, manager: CronotermostatoZoneManager, entry: ConfigEntry) -> None:
        self.manager = manager
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_button_apply_now"
        self._attr_device_info = manager.device_info

    async def async_press(self) -> None:
        """Forza l'applicazione della fascia corrente."""
        _LOGGER.info("Zona '%s': Pressione pulsante 'Applica Fascia Corrente'", self.manager.zone_name)
        await self.manager._async_apply_current_slot()
