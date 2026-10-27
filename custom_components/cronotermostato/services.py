"""Registrazione dei servizi personalizzati per Cronotermostato Multizona."""

from __future__ import annotations

from datetime import datetime, time
import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_PRESET,
    ATTR_SLOT_NUMBER,
    ATTR_TIME,
    ATTR_ZONE_ID,
    DEFAULT_PRESET_OPTIONS,
    DOMAIN,
    SERVICE_APPLY_NOW,
    SERVICE_SET_SLOT,
)

_LOGGER = logging.getLogger(__name__)

SCHEMA_APPLY_NOW = vol.Schema(
    {
        vol.Required(ATTR_ZONE_ID): cv.string,
    }
)

SCHEMA_SET_SLOT = vol.Schema(
    {
        vol.Required(ATTR_ZONE_ID): cv.string,
        vol.Required(ATTR_SLOT_NUMBER): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
        vol.Optional(ATTR_TIME): cv.time,
        vol.Optional(ATTR_PRESET): vol.In(DEFAULT_PRESET_OPTIONS),
    }
)


async def async_register_services(hass: HomeAssistant) -> None:
    """Registra i servizi del dominio cronotermostato."""

    async def async_handle_apply_now(call: ServiceCall) -> None:
        """Forza l'applicazione della fascia attiva per una zona."""
        zone_id = call.data[ATTR_ZONE_ID]
        manager = _find_manager(hass, zone_id)
        if not manager:
            _LOGGER.error("Zona '%s' non trovata", zone_id)
            return
        await manager._async_apply_current_slot()

    async def async_handle_set_slot(call: ServiceCall) -> None:
        """Modifica orario e/o preset di una specifica fascia."""
        zone_id = call.data[ATTR_ZONE_ID]
        slot_number = call.data[ATTR_SLOT_NUMBER]
        new_time: time | None = call.data.get(ATTR_TIME)
        new_preset: str | None = call.data.get(ATTR_PRESET)

        manager = _find_manager(hass, zone_id)
        if not manager:
            _LOGGER.error("Zona '%s' non trovata", zone_id)
            return

        slot = manager.slots.get(slot_number)
        if not slot:
            _LOGGER.error("Fascia %d non configurata per la zona '%s'", slot_number, zone_id)
            return

        if new_time is not None:
            slot.time = new_time
        if new_preset is not None:
            slot.preset = new_preset

        manager._notify_listeners()
        _LOGGER.info(
            "Zona '%s': Fascia %d aggiornata (Orario: %s, Preset: %s)",
            manager.zone_name,
            slot_number,
            slot.time.strftime("%H:%M"),
            slot.preset,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_APPLY_NOW):
        hass.services.async_register(
            DOMAIN, SERVICE_APPLY_NOW, async_handle_apply_now, schema=SCHEMA_APPLY_NOW
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_SLOT):
        hass.services.async_register(
            DOMAIN, SERVICE_SET_SLOT, async_handle_set_slot, schema=SCHEMA_SET_SLOT
        )


def _find_manager(hass: HomeAssistant, zone_identifier: str):
    """Cerca il manager per entry_id o per nome zona."""
    domain_data = hass.data.get(DOMAIN, {})
    # Match diretto per entry_id
    if zone_identifier in domain_data:
        return domain_data[zone_identifier]

    # Match per nome zona (case-insensitive)
    for manager in domain_data.values():
        if manager.zone_name.lower() == zone_identifier.lower():
            return manager

    return None
