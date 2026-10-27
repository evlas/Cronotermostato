"""Piattaforma Switch per comandi e abilitazioni del Cronotermostato."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import CronotermostatoZoneManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura gli switch per la zona del cronotermostato."""
    manager: CronotermostatoZoneManager = hass.data[DOMAIN][entry.entry_id]

    switches: list[SwitchEntity] = [
        CronotermostatoMasterSwitch(manager, entry),
        CronotermostatoAutoSwitch(manager, entry),
    ]

    # Aggiungi lo switch per la zona notte solo se ci sono climate secondari configurati
    if manager.secondary_climate_entities:
        switches.append(CronotermostatoSecondarySummerSwitch(manager, entry))

    async_add_entities(switches)


class CronotermostatoBaseSwitch(RestoreEntity, SwitchEntity):
    """Classe base per gli switch del cronotermostato."""

    _attr_has_entity_name = True

    def __init__(self, manager: CronotermostatoZoneManager, entry: ConfigEntry) -> None:
        """Inizializza lo switch."""
        self.manager = manager
        self.entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Cronotermostato {manager.zone_name}",
            manufacturer="evlas",
            model="Cronotermostato Multizona",
            sw_version="1.0.0",
        )

    async def async_added_to_hass(self) -> None:
        """Registra il listener per aggiornamenti dello stato."""
        await super().async_added_to_hass()
        self.async_on_remove(self.manager.async_add_listener(self.async_write_ha_state))


class CronotermostatoMasterSwitch(CronotermostatoBaseSwitch):
    """Switch principale per abilitare/disabilitare la programmazione oraria (ex crono_pt)."""

    def __init__(self, manager: CronotermostatoZoneManager, entry: ConfigEntry) -> None:
        super().__init__(manager, entry)
        self._attr_name = "Abilitazione Cronotermostato"
        self._attr_unique_id = f"{entry.entry_id}_switch_crono_master"
        self._attr_icon = "mdi:calendar-clock"

    @property
    def is_on(self) -> bool:
        return self.manager.crono_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.manager.crono_enabled = True
        self.manager._notify_listeners()
        # Se riattivato, applica subito la fascia corrispondente
        await self.manager._async_apply_current_slot()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.manager.crono_enabled = False
        self.manager._notify_listeners()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state:
            self.manager.crono_enabled = last_state.state == "on"


class CronotermostatoAutoSwitch(CronotermostatoBaseSwitch):
    """Switch per la termoregolazione automatica (ex termoregolazioneautopt)."""

    def __init__(self, manager: CronotermostatoZoneManager, entry: ConfigEntry) -> None:
        super().__init__(manager, entry)
        self._attr_name = "Termoregolazione Automatica"
        self._attr_unique_id = f"{entry.entry_id}_switch_auto"
        self._attr_icon = "mdi:thermostat-auto"

    @property
    def is_on(self) -> bool:
        return self.manager.auto_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.manager.auto_enabled = True
        self.manager._notify_listeners()
        await self.manager._async_apply_current_slot()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.manager.auto_enabled = False
        self.manager._notify_listeners()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state:
            self.manager.auto_enabled = last_state.state == "on"


class CronotermostatoSecondarySummerSwitch(CronotermostatoBaseSwitch):
    """Switch per includere la zona secondaria/notte nel ciclo estivo."""

    def __init__(self, manager: CronotermostatoZoneManager, entry: ConfigEntry) -> None:
        super().__init__(manager, entry)
        self._attr_name = "Zona Secondaria/Notte Partecipa in Estate"
        self._attr_unique_id = f"{entry.entry_id}_switch_secondary_summer"
        self._attr_icon = "mdi:bed"

    @property
    def is_on(self) -> bool:
        return self.manager.secondary_participates_summer

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.manager.secondary_participates_summer = True
        self.manager._notify_listeners()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.manager.secondary_participates_summer = False
        self.manager._notify_listeners()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state:
            self.manager.secondary_participates_summer = last_state.state == "on"
