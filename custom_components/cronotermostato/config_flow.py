"""Config Flow per l'integrazione Cronotermostato Multizona."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.util import slugify

from .const import (
    CONF_CLIMATE_ENTITIES,
    CONF_RESTORE_ON_STARTUP,
    CONF_SEASON_INVERT,
    CONF_SEASON_SWITCH,
    CONF_SECONDARY_CLIMATE_ENTITIES,
    CONF_SLOTS_COUNT,
    CONF_ZONE_NAME,
    DEFAULT_RESTORE_ON_STARTUP,
    DEFAULT_SEASON_INVERT,
    DEFAULT_SLOTS_COUNT,
    DEFAULT_ZONE_NAME,
    DOMAIN,
    MAX_SLOTS_COUNT,
    MIN_SLOTS_COUNT,
)

_LOGGER = logging.getLogger(__name__)


class CronotermostatoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce il Config Flow per aggiungere nuove zone."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Primo step: configurazione della zona."""
        errors: dict[str, str] = {}

        if user_input is not None:
            zone_name = user_input[CONF_ZONE_NAME].strip()
            unique_id = f"cronotermostato_{slugify(zone_name)}"

            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            if not user_input.get(CONF_CLIMATE_ENTITIES):
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
            # Aggiorna la entry
            new_data = dict(self.config_entry.data)
            new_data.update(user_input)
            self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
            return self.async_create_entry(title="", data={})

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
                    CONF_RESTORE_ON_STARTUP,
                    default=data.get(CONF_RESTORE_ON_STARTUP, DEFAULT_RESTORE_ON_STARTUP),
                ): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
