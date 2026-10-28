"""Piattaforma Sensori per il monitoraggio dello stato del Cronotermostato."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ZONE_MODES
from .coordinator import CronotermostatoZoneManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura i sensori diagnostici della zona."""
    manager: CronotermostatoZoneManager = hass.data[DOMAIN][entry.entry_id]

    sensors: list[SensorEntity] = [
        CronotermostatoActiveSlotSensor(manager, entry),
        CronotermostatoNextSlotSensor(manager, entry),
        CronotermostatoStatusSensor(manager, entry),
    ]

    async_add_entities(sensors)


class CronotermostatoBaseSensor(SensorEntity):
    """Classe base per i sensori del cronotermostato."""

    _attr_has_entity_name = True

    def __init__(self, manager: CronotermostatoZoneManager, entry: ConfigEntry) -> None:
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
        await super().async_added_to_hass()
        self.async_on_remove(self.manager.async_add_listener(self.async_write_ha_state))


class CronotermostatoActiveSlotSensor(CronotermostatoBaseSensor):
    """Sensore che indica la fascia oraria attualmente in esecuzione."""

    _attr_translation_key = "active_slot"
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, manager: CronotermostatoZoneManager, entry: ConfigEntry) -> None:
        super().__init__(manager, entry)
        self._attr_unique_id = f"{entry.entry_id}_sensor_active_slot"

    @property
    def native_value(self) -> str:
        if self.manager.active_slot is None:
            return "none"
        return f"Slot {self.manager.active_slot} ({self.manager.last_applied_preset})"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "slot_index": self.manager.active_slot,
            "applied_preset": self.manager.last_applied_preset,
            "last_applied": (
                self.manager.last_applied_time.strftime("%d/%m/%Y %H:%M:%S")
                if self.manager.last_applied_time
                else None
            ),
            "controlled_climates": self.manager.get_target_climates(),
            "season": "winter" if self.manager.is_winter() else "summer",
            "season_switch": self.manager.season_switch,
            "season_invert": self.manager.season_invert,
        }


class CronotermostatoNextSlotSensor(CronotermostatoBaseSensor):
    """Sensore che indica la prossima fascia programmata in arrivo."""

    _attr_translation_key = "next_slot"
    _attr_icon = "mdi:clock-fast"

    def __init__(self, manager: CronotermostatoZoneManager, entry: ConfigEntry) -> None:
        super().__init__(manager, entry)
        self._attr_unique_id = f"{entry.entry_id}_sensor_next_slot"

    @property
    def native_value(self) -> str:
        idx, t, preset = self.manager.get_next_slot_info()
        if idx is None or t is None:
            return "none"
        return f"Slot {idx} @ {t.strftime('%H:%M')} ({preset})"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        idx, t, preset = self.manager.get_next_slot_info()
        return {
            "next_slot_index": idx,
            "next_time": t.strftime("%H:%M") if t else None,
            "next_preset": preset,
        }


class CronotermostatoStatusSensor(CronotermostatoBaseSensor):
    """Sensore diagnostico sullo stato globale della zona."""

    _attr_translation_key = "zone_status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ZONE_MODES
    _attr_icon = "mdi:information-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, manager: CronotermostatoZoneManager, entry: ConfigEntry) -> None:
        super().__init__(manager, entry)
        self._attr_unique_id = f"{entry.entry_id}_sensor_status"

    @property
    def native_value(self) -> str:
        return self.manager.mode

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "last_message": self.manager.last_action_message,
            "crono_enabled": self.manager.crono_enabled,
            "auto_enabled": self.manager.auto_enabled,
            "is_winter": self.manager.is_winter(),
            "main_climates": self.manager.climate_entities,
            "secondary_climates": self.manager.secondary_climate_entities,
            "slots_count": self.manager.slots_count,
            "knx_scene_in_casa": self.manager.knx_scene_in_casa,
            "knx_scene_uscita": self.manager.knx_scene_uscita,
            "knx_scene_notte": self.manager.knx_scene_notte,
            "knx_scene_vacanza": self.manager.knx_scene_vacanza,
            "knx_scene_sensor": self.manager.knx_scene_sensor,
            "off_preset": self.manager.off_preset,
        }
