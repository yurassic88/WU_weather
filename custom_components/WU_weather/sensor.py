"""Platform for sensor integration for Combined Weather."""
from __future__ import annotations
import logging
from datetime import timedelta, datetime

import voluptuous as vol
import requests
from bs4 import BeautifulSoup

from homeassistant.components.sensor import (
    SensorEntity,
    PLATFORM_SCHEMA,
)
from homeassistant.const import UnitOfTemperature
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
SCAN_INTERVAL = timedelta(minutes=5)


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


import requests
from bs4 import BeautifulSoup
import json

class _LOGGER:
    def error(error):
        print(error)
    def info(msg):
        print(msg)


class WUWeatherSensor (SensorEntity):
    """Representation of the Combined Weather Sensor."""

    def __init__(self, name, current_weather_url, forecast_url=""):
        """Initialize the sensor."""
        self._name = name
        self._current_weather_url = current_weather_url
        self._forecast_url = forecast_url
        self._state = None
        self._attributes = {'dew_point': 11.67,
                            'apparent_temperature': 14.2,
                            'precipitation': 0,
                            'precipitation_unit': 'mm',
                            'temperature': 14.22,
                            'temperature_unit': '°C',
                            'wind_speed': 2.57,
                            'wind_speed_unit': 'km/h',
                            'wind_gust_speed': 3.70,
                            'pressure': 1013,
                            'humidity': 86,
                            'wind_bearing': 150,
                            'uv_index': 1,
                            'latest_update': 'n/a'}

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
        return UnitOfTemperature.CELSIUS

    @property
    def extra_state_attributes(self):
        """Return other details about the sensor as attributes."""
        return self._attributes

    def FtoC(self, temp):
        return (temp-32)*5/9

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        _LOGGER.info("WU update triggered")
        # --- Current Weather Scraping ---
        # ** REPLACE THIS SECTION WITH YOUR ACTUAL SCRAPING LOGIC **
        try:
            # Make a request to the current weather URL
            current_page = requests.get(self._current_weather_url, timeout=10)
            current_page.raise_for_status() # Raise an exception for bad status codes
            current_soup = BeautifulSoup(current_page.content, "html.parser")
            _LOGGER.info("WU request fulfiled")
            # Example: Scrape temperature (replace with your actual element and class)
            # Find the HTML element containing the temperature and extract its text.
            temp_element = current_soup.find("script", id="app-root-state")
            try:
                json_object = json.loads(temp_element.get_text())
                for k in json_object.keys():
                    if 'b' in json_object[k] and 'summaries' in json_object[k]['b']:
                        weather_summary = json_object[k]['b']['summaries'][0]
                        # apparent_temperature: 12.0
                        # cloud_coverage: 0
                        # dew_point: 5.0
                        # humidity: 76
                        # precipitation_unit: mm
                        # pressure: 1019
                        # pressure_unit: hPa
                        # temperature: 14.2
                        # temperature_unit: °C
                        # uv_index: 2
                        # visibility: 10
                        # visibility_unit: km
                        # wind_bearing: 260
                        # wind_gust_speed: 51.56
                        # wind_speed: 35.17
                        # wind_speed_unit: km/h
                        if "imperial" in weather_summary:
                            if "dewptAvg" in weather_summary['imperial']:
                                print(weather_summary['imperial']['dewptAvg'])
                                self._attributes["dew_point"] = self.FtoC(weather_summary['imperial']['dewptAvg'])

                            if "windchillAvg" in weather_summary['imperial']:
                                self._attributes["apparent_temperature"] = self.FtoC(weather_summary['imperial']['windchillAvg'])

                            if "precipRate" in weather_summary['imperial']:
                                self._attributes["precipitation"] = weather_summary['imperial']['precipRate']
                                self._attributes["precipitation_unit"] = "mm"

                            if "tempAvg" in weather_summary['imperial']:
                                self._attributes["temperature"] = self.FtoC(weather_summary['imperial']['tempAvg'])
                                self._attributes["temperature_unit"] = "°C"

                            if "windspeedAvg" in weather_summary['imperial']:
                                self._attributes["wind_speed"] = weather_summary['imperial']['windspeedAvg']*1.60934
                                self._attributes["wind_speed_unit"] = "km/h"

                            if "windgustAvg" in weather_summary['imperial']:
                                self._attributes["wind_gust_speed"] = weather_summary['imperial']['windgustAvg']*1.60934

                            if "pressureMax" in weather_summary['imperial']:
                                self._attributes["pressure"] = weather_summary['imperial']['pressureMax']*33.86389

                        if 'humidityAvg' in weather_summary:
                            self._attributes["humidity"] = weather_summary['humidityAvg']

                        if 'winddirAvg' in weather_summary:
                            self._attributes["wind_bearing"] = weather_summary['winddirAvg']

                        if 'uvHigh' in weather_summary:
                            self._attributes["uv_index"] = weather_summary['uvHigh']

                        self._attributes['latest_update'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

            except ValueError as e:
                _LOGGER.error("Error fetching current weather data: %s", e)
                self._state = None # Set to unavailable on error
                return # Stop the update if the first source fails

        except requests.exceptions.RequestException as e:
            _LOGGER.error("Error fetching current weather data: %s", e)
            self._state = None # Set to unavailable on error
            return # Stop the update if the first source fails

        # --- Forecast Scraping ---
        # ** REPLACE THIS SECTION WITH YOUR ACTUAL SCRAPING LOGIC **
        # try:
        #     # Make a request to the forecast URL
        #     forecast_page = requests.get(self._forecast_url, timeout=10)
        #     forecast_page.raise_for_status()
        #     forecast_soup = BeautifulSoup(forecast_page.content, "html.parser")

        #     # Example: Scrape forecast for the next 3 days
        #     forecasts = []
        #     # Find all parent elements for a daily forecast
        #     for day in forecast_soup.find_all("div", class_="forecast-day-class", limit=3):
        #         date = day.find("span", class_="date-class").text
        #         temp_high = day.find("span", class_="temp-high-class").text
        #         temp_low = day.find("span", class_="temp-low-class").text
        #         condition = day.find("span", class_="condition-class").text
        #         forecasts.append({
        #             "date": date.strip(),
        #             "temp_high": temp_high.strip(),
        #             "temp_low": temp_low.strip(),
        #             "condition": condition.strip(),
        #         })
        #     self._attributes["forecast"] = forecasts

        # except requests.exceptions.RequestException as e:
        #     _LOGGER.error("Error fetching forecast data: %s", e)
        #     self._attributes["forecast"] = None # Set forecast to unavailable on error