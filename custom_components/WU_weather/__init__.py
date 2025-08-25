"""The Combined Weather integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN

# List of platforms that this integration will create.
#PLATFORMS: list[Platform] = [Platform.SENSOR]#, Platform.WEATHER]
PLATFORMS: list[Platform] = [Platform.WEATHER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Combined Weather from a config entry."""
    # Forward the setup to the sensor platform.
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload the sensor platform when the integration is removed.
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)