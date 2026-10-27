"""Inizializzazione del componente Cronotermostato Multizona."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import CronotermostatoZoneManager
from .services import async_register_services

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configura una zona del cronotermostato da config entry."""
    hass.data.setdefault(DOMAIN, {})

    manager = CronotermostatoZoneManager(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = manager

    await manager.async_setup()

    # Inoltra il setup alle piattaforme supportate
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Registra i servizi
    await async_register_services(hass)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _LOGGER.info("Zona Cronotermostato '%s' avviata con successo", manager.zone_name)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Rimuove una zona del cronotermostato."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        manager: CronotermostatoZoneManager = hass.data[DOMAIN].pop(entry.entry_id)
        await manager.async_unload()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Ricarica la configurazione della zona."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
