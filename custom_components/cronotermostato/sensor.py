"""Piattaforma Sensori per il monitoraggio dello stato del Cronotermostato."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
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

    def __init__(self, manager: CronotermostatoZoneManager, entry: ConfigEntry) -> None:
        super().__init__(manager, entry)
        self._attr_name = "Fascia Attiva"
        self._attr_unique_id = f"{entry.entry_id}_sensor_active_slot"
        self._attr_icon = "mdi:clock-check-outline"

    @property
    def native_value(self) -> str:
        if self.manager.active_slot is None:
            return "Nessuna"
        return f"Fascia {self.manager.active_slot} ({self.manager.last_applied_preset})"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "slot_index": self.manager.active_slot,
            "preset_applicato": self.manager.last_applied_preset,
            "ultimo_aggiornamento": (
                self.manager.last_applied_time.strftime("%d/%m/%Y %H:%M:%S")
                if self.manager.last_applied_time
                else None
            ),
            "clima_attualmente_comandati": self.manager.get_target_climates(),
            "stagione": "Inverno" if self.manager.is_winter() else "Estate",
        }


class CronotermostatoNextSlotSensor(CronotermostatoBaseSensor):
    """Sensore che indica la prossima fascia programmata in arrivo."""

    def __init__(self, manager: CronotermostatoZoneManager, entry: ConfigEntry) -> None:
        super().__init__(manager, entry)
        self._attr_name = "Prossima Fascia"
        self._attr_unique_id = f"{entry.entry_id}_sensor_next_slot"
        self._attr_icon = "mdi:clock-fast"

    @property
    def native_value(self) -> str:
        idx, t, preset = self.manager.get_next_slot_info()
        if idx is None or t is None:
            return "Nessuna"
        return f"Fascia {idx} alle {t.strftime('%H:%M')} ({preset})"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        idx, t, preset = self.manager.get_next_slot_info()
        return {
            "prossimo_slot_index": idx,
            "prossimo_orario": t.strftime("%H:%M") if t else None,
            "prossimo_preset": preset,
        }


class CronotermostatoStatusSensor(CronotermostatoBaseSensor):
    """Sensore diagnostico sullo stato globale della zona."""

    def __init__(self, manager: CronotermostatoZoneManager, entry: ConfigEntry) -> None:
        super().__init__(manager, entry)
        self._attr_name = "Stato Zona"
        self._attr_unique_id = f"{entry.entry_id}_sensor_status"
        self._attr_icon = "mdi:information-outline"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str:
        if not self.manager.crono_enabled:
            return "Crono Disabilitato"
        if not self.manager.auto_enabled:
            return "Termoregolazione Off"
        return "Attivo"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "ultimo_messaggio": self.manager.last_action_message,
            "inverno_attivo": self.manager.is_winter(),
            "entita_principali": self.manager.climate_entities,
            "entita_secondarie": self.manager.secondary_climate_entities,
            "numero_fasce": self.manager.slots_count,
        }
