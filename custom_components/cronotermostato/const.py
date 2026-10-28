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

# Chiavi di configurazione zona
CONF_ZONE_NAME = "zone_name"
CONF_CLIMATE_ENTITIES = "climate_entities"
CONF_SECONDARY_CLIMATE_ENTITIES = "secondary_climate_entities"
CONF_SEASON_SWITCH = "season_switch"
CONF_SEASON_INVERT = "season_invert"
CONF_SLOTS_COUNT = "slots_count"
CONF_RESTORE_ON_STARTUP = "restore_on_startup"

# Chiavi di configurazione Scene / Presenza e Spegnimento
CONF_SCENE_SENSOR = "scene_sensor"
CONF_KNX_SCENE_SENSOR = "knx_scene_sensor"  # Deprecato ma mantenuto per retrocompatibilità
CONF_KNX_SCENE_IN_CASA = "knx_scene_in_casa"
CONF_KNX_SCENE_USCITA = "knx_scene_uscita"
CONF_KNX_SCENE_NOTTE = "knx_scene_notte"
CONF_KNX_SCENE_VACANZA = "knx_scene_vacanza"
CONF_OFF_PRESET = "off_preset"

# Valori predefiniti
DEFAULT_ZONE_NAME = "Zona"
DEFAULT_SLOTS_COUNT = 5
MIN_SLOTS_COUNT = 1
MAX_SLOTS_COUNT = 10
DEFAULT_SEASON_INVERT = False  # Nel package: switch.inverno_estate: on=Inverno, off=Estate
DEFAULT_RESTORE_ON_STARTUP = True

# Modalità operative globali della zona
MODE_CRONOTERMOSTATO = "cronotermostato"
MODE_SCENE = "scene"
MODE_SCENE_KNX = "scene"  # Alias per retrocompatibilità
MODE_MANUALE = "manuale"
MODE_OFF = "off"

ZONE_MODES = [
    MODE_CRONOTERMOSTATO,
    MODE_SCENE,
    MODE_MANUALE,
    MODE_OFF,
]

# Preset supportati dai termostati
PRESET_NONE = "none"
PRESET_COMFORT = "comfort"
PRESET_STANDBY = "standby"
PRESET_ECONOMY = "economy"
PRESET_BUILDING_PROTECTION = "building_protection"
PRESET_AWAY = "away"
PRESET_ECO = "eco"
PRESET_BOOST = "boost"

DEFAULT_PRESET_OPTIONS = [
    PRESET_COMFORT,
    PRESET_STANDBY,
    PRESET_ECONOMY,
    PRESET_BUILDING_PROTECTION,
]

# Mappatura universale sensore di scena/presenza (ad es. sensor.ultima_scena)
SCENE_PRESET_MAPPING: dict[str, list[str]] = {
    PRESET_COMFORT: ["in casa", "in_casa", "home", "comfort"],
    PRESET_STANDBY: ["uscita", "away", "standby", "eco"],
    PRESET_ECONOMY: ["notte", "night", "sleep", "economy"],
    PRESET_BUILDING_PROTECTION: ["vacanza", "holiday", "protezione", "building_protection"],
}

DEFAULT_OFF_PRESET = PRESET_BUILDING_PROTECTION

# Servizi
SERVICE_APPLY_NOW = "apply_now"
SERVICE_SET_SLOT = "set_slot"
SERVICE_SET_ZONE_MODE = "set_zone_mode"
ATTR_ZONE_ID = "zone_id"
ATTR_SLOT_NUMBER = "slot_number"
ATTR_TIME = "time"
ATTR_PRESET = "preset"
ATTR_MODE = "mode"
