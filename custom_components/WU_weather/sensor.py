"""Platform for sensor integration for Combined Weather."""
from __future__ import annotations
import logging
from datetime import timedelta

import voluptuous as vol
import requests
from bs4 import BeautifulSoup

from homeassistant.components.sensor import (
    SensorEntity,
    PLATFORM_SCHEMA,
)
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

# --- Configuration Schema for configuration.yaml (Legacy) ---
# This allows users to configure the sensor via YAML if they prefer.
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required("current_weather_url"): cv.string,
    vol.Required("forecast_url"): cv.string,
    vol.Optional("name", default="WU_Weather"): cv.string,
})

# --- Update Interval ---
# Defines how often the sensor will fetch new data.
SCAN_INTERVAL = timedelta(minutes=15)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform from configuration.yaml."""
    name = config.get("name")
    current_weather_url = config.get("current_weather_url")
    forecast_url = config.get("forecast_url")

    # Create the sensor entity and add it to Home Assistant.
    add_entities([WUWeatherSensor(name, current_weather_url, forecast_url)])


class WUWeatherSensor(SensorEntity):
    """Representation of the Combined Weather Sensor."""

    def __init__(self, name, current_weather_url, forecast_url):
        """Initialize the sensor."""
        self._name = name
        self._current_weather_url = current_weather_url
        self._forecast_url = forecast_url
        self._state = None
        self._attributes = {}

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor (e.g., the current temperature)."""
        return self._state

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement for the state."""
        return TEMP_CELSIUS

    @property
    def extra_state_attributes(self):
        """Return other details about the sensor as attributes."""
        return self._attributes

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        
        # --- Current Weather Scraping ---
        # ** REPLACE THIS SECTION WITH YOUR ACTUAL SCRAPING LOGIC **
        try:
            # Make a request to the current weather URL
            current_page = requests.get(self._current_weather_url, timeout=10)
            current_page.raise_for_status() # Raise an exception for bad status codes
            current_soup = BeautifulSoup(current_page.content, "html.parser")
            
            # Example: Scrape temperature (replace with your actual element and class)
            # Find the HTML element containing the temperature and extract its text.
            temp_element = current_soup.find("span", class_="temperature-class")
            if temp_element:
                temperature = temp_element.text
                self._state = temperature.replace("°C", "").strip()
            else:
                _LOGGER.warning("Could not find temperature element on current weather page.")
                self._state = None


            # Example: Scrape humidity (replace with your actual element and class)
            humidity_element = current_soup.find("span", class_="humidity-class")
            if humidity_element:
                 self._attributes["humidity"] = humidity_element.text.strip()

        except requests.exceptions.RequestException as e:
            _LOGGER.error("Error fetching current weather data: %s", e)
            self._state = None # Set to unavailable on error
            return # Stop the update if the first source fails

        # --- Forecast Scraping ---
        # ** REPLACE THIS SECTION WITH YOUR ACTUAL SCRAPING LOGIC **
        try:
            # Make a request to the forecast URL
            forecast_page = requests.get(self._forecast_url, timeout=10)
            forecast_page.raise_for_status()
            forecast_soup = BeautifulSoup(forecast_page.content, "html.parser")

            # Example: Scrape forecast for the next 3 days
            forecasts = []
            # Find all parent elements for a daily forecast
            for day in forecast_soup.find_all("div", class_="forecast-day-class", limit=3):
                date = day.find("span", class_="date-class").text
                temp_high = day.find("span", class_="temp-high-class").text
                temp_low = day.find("span", class_="temp-low-class").text
                condition = day.find("span", class_="condition-class").text
                forecasts.append({
                    "date": date.strip(),
                    "temp_high": temp_high.strip(),
                    "temp_low": temp_low.strip(),
                    "condition": condition.strip(),
                })
            self._attributes["forecast"] = forecasts

        except requests.exceptions.RequestException as e:
            _LOGGER.error("Error fetching forecast data: %s", e)
            self._attributes["forecast"] = None # Set forecast to unavailable on error