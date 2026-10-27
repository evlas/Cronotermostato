"""Costanti per l'integrazione Cronotermostato Multizona."""

from homeassistant.const import Platform

DOMAIN = "cronotermostato"
NAME = "Cronotermostato Multizona"

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.TIME,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.BUTTON,
]

# Chiavi di configurazione
CONF_ZONE_NAME = "zone_name"
CONF_CLIMATE_ENTITIES = "climate_entities"
CONF_SECONDARY_CLIMATE_ENTITIES = "secondary_climate_entities"
CONF_SEASON_SWITCH = "season_switch"
CONF_SEASON_INVERT = "season_invert"
CONF_SLOTS_COUNT = "slots_count"
CONF_RESTORE_ON_STARTUP = "restore_on_startup"

# Valori predefiniti
DEFAULT_ZONE_NAME = "Zona"
DEFAULT_SLOTS_COUNT = 5
MIN_SLOTS_COUNT = 1
MAX_SLOTS_COUNT = 10
DEFAULT_SEASON_INVERT = False  # Nel package: switch.inverno_estate: on=Inverno, off=Estate
DEFAULT_RESTORE_ON_STARTUP = True

# Modalità e preset termostato
PRESET_NONE = "NONE"
PRESET_COMFORT = "comfort"
PRESET_STANDBY = "standby"
PRESET_ECONOMY = "economy"
PRESET_BUILDING_PROTECTION = "building_protection"
PRESET_ECO = "eco"
PRESET_BOOST = "boost"

DEFAULT_PRESET_OPTIONS = [
    PRESET_NONE,
    PRESET_COMFORT,
    PRESET_STANDBY,
    PRESET_ECONOMY,
    PRESET_BUILDING_PROTECTION,
    PRESET_ECO,
    PRESET_BOOST,
]

# Servizi
SERVICE_APPLY_NOW = "apply_now"
SERVICE_SET_SLOT = "set_slot"
ATTR_ZONE_ID = "zone_id"
ATTR_SLOT_NUMBER = "slot_number"
ATTR_TIME = "time"
ATTR_PRESET = "preset"
