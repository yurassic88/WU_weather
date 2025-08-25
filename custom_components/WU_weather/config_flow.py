"""Config flow for Combined Weather integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN


class WUWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Combined Weather."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial user setup step."""
        errors = {}
        if user_input is not None:
            # You can add validation here to check if URLs are valid etc.
            # For now, we assume they are correct.
            return self.async_create_entry(title=user_input["name"], data=user_input)

        # Show the form to the user.
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default="WU_weather"): str,
                    vol.Required("current_weather_url"): str,
                    vol.Required("forecast_url"): str,
                }
            ),
            errors=errors,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Combined Weather."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options for the integration."""
        if user_input is not None:
            # Update the config entry with new options.
            return self.async_create_entry(title="", data=user_input)

        # Show the options form, pre-filled with current values.
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "current_weather_url",
                        default=self.config_entry.data.get("current_weather_url"),
                    ): str,
                    vol.Required(
                        "forecast_url",
                        default=self.config_entry.data.get("forecast_url"),
                    ): str,
                }
            ),
        )
