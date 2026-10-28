"""Config Flow per l'integrazione Cronotermostato Multizona."""

from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_CLIMATE_ENTITIES,
    CONF_KNX_SCENE_SENSOR,
    CONF_OFF_PRESET,
    CONF_RESTORE_ON_STARTUP,
    CONF_SCENE_SENSOR,
    CONF_SEASON_INVERT,
    CONF_SEASON_SWITCH,
    CONF_SECONDARY_CLIMATE_ENTITIES,
    CONF_SLOTS_COUNT,
    CONF_ZONE_NAME,
    DEFAULT_OFF_PRESET,
    DEFAULT_PRESET_OPTIONS,
    DEFAULT_RESTORE_ON_STARTUP,
    DEFAULT_SEASON_INVERT,
    DEFAULT_SLOTS_COUNT,
    DEFAULT_ZONE_NAME,
    DOMAIN,
    MAX_SLOTS_COUNT,
    MIN_SLOTS_COUNT,
)


class CronotermostatoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce il Config Flow per l'integrazione Cronotermostato."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configurazione di una nuova zona del cronotermostato."""
        errors: dict[str, str] = {}

        if user_input is not None:
            zone_name = user_input.get(CONF_ZONE_NAME, DEFAULT_ZONE_NAME).strip()
            unique_id = f"cronotermostato_{zone_name.lower().replace(' ', '_')}"

            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            # Valida che sia stato selezionato almeno un termostato
            climates = user_input.get(CONF_CLIMATE_ENTITIES, [])
            if not climates:
                errors[CONF_CLIMATE_ENTITIES] = "no_climate_selected"

            if not errors:
                return self.async_create_entry(
                    title=f"Cronotermostato: {zone_name}",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_ZONE_NAME, default=DEFAULT_ZONE_NAME): str,
                vol.Required(CONF_CLIMATE_ENTITIES): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="climate", multiple=True)
                ),
                vol.Optional(CONF_SECONDARY_CLIMATE_ENTITIES, default=[]): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="climate", multiple=True)
                ),
                vol.Optional(CONF_SEASON_SWITCH): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["switch", "input_boolean"], multiple=False)
                ),
                vol.Optional(CONF_SEASON_INVERT, default=DEFAULT_SEASON_INVERT): bool,
                vol.Required(
                    CONF_SLOTS_COUNT, default=DEFAULT_SLOTS_COUNT
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_SLOTS_COUNT,
                        max=MAX_SLOTS_COUNT,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(CONF_SCENE_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor", "input_select", "select"], multiple=False)
                ),
                vol.Optional(
                    CONF_OFF_PRESET, default=DEFAULT_OFF_PRESET
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=DEFAULT_PRESET_OPTIONS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="preset_options",
                    )
                ),
                vol.Optional(
                    CONF_RESTORE_ON_STARTUP, default=DEFAULT_RESTORE_ON_STARTUP
                ): bool,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Restituisce l'handler per modificare le opzioni della zona."""
        return CronotermostatoOptionsFlowHandler(config_entry)


class CronotermostatoOptionsFlowHandler(config_entries.OptionsFlow):
    """Gestisce le opzioni di modifica della zona."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Inizializza l'handler opzioni."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Form per aggiornare le opzioni della zona."""
        errors: dict[str, str] = {}
        data = self.config_entry.data

        if user_input is not None:
            new_data = dict(self.config_entry.data)
            new_data.update(user_input)
            self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
            return self.async_create_entry(title="", data={})

        current_scene_sensor = data.get(CONF_SCENE_SENSOR) or data.get(CONF_KNX_SCENE_SENSOR)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_CLIMATE_ENTITIES,
                    default=data.get(CONF_CLIMATE_ENTITIES, []),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="climate", multiple=True)
                ),
                vol.Optional(
                    CONF_SECONDARY_CLIMATE_ENTITIES,
                    default=data.get(CONF_SECONDARY_CLIMATE_ENTITIES, []),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="climate", multiple=True)
                ),
                vol.Optional(
                    CONF_SEASON_SWITCH,
                    description={"suggested_value": data.get(CONF_SEASON_SWITCH)},
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["switch", "input_boolean"], multiple=False)
                ),
                vol.Optional(
                    CONF_SEASON_INVERT,
                    default=data.get(CONF_SEASON_INVERT, DEFAULT_SEASON_INVERT),
                ): bool,
                vol.Required(
                    CONF_SLOTS_COUNT,
                    default=data.get(CONF_SLOTS_COUNT, DEFAULT_SLOTS_COUNT),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_SLOTS_COUNT,
                        max=MAX_SLOTS_COUNT,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_SCENE_SENSOR,
                    description={"suggested_value": current_scene_sensor},
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor", "input_select", "select"], multiple=False)
                ),
                vol.Optional(
                    CONF_OFF_PRESET,
                    default=data.get(CONF_OFF_PRESET, DEFAULT_OFF_PRESET),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=DEFAULT_PRESET_OPTIONS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="preset_options",
                    )
                ),
                vol.Optional(
                    CONF_RESTORE_ON_STARTUP,
                    default=data.get(CONF_RESTORE_ON_STARTUP, DEFAULT_RESTORE_ON_STARTUP),
                ): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
