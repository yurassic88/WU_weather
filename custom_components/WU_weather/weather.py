"""Platform for weather integration."""
from __future__ import annotations
import logging
from datetime import timedelta

import voluptuous as vol
import requests
from bs4 import BeautifulSoup

from homeassistant.components.weather import (
    WeatherEntity,
    PLATFORM_SCHEMA,
    WeatherEntityFeature,
)
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfSpeed,
    UnitOfPressure,
    UnitOfLength,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

# Define the configuration schema for configuration.yaml
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required("current_weather_url"): cv.string,
    vol.Optional("name", default="WU Weather"): cv.string,
})

# Define the update interval for the coordinator
SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the weather platform."""
    current_weather_url = config.get("current_weather_url")
    name = config.get("name")

    coordinator = WeatherUpdateCoordinator(hass, current_weather_url)
    
    # Manually trigger the first refresh
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([WUWeather(coordinator, name)])


class WeatherUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching WU data."""

    def __init__(self, hass, current_weather_url):
        """Initialize."""
        self.url = current_weather_url

        super().__init__(
            hass,
            _LOGGER,
            name="WU Weather",
            update_interval=SCAN_INTERVAL,
        )

    def _fetch_data(self, url):
        """Fetch data from a URL in a blocking way."""
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def _async_update_data(self):
        """Fetch data from API endpoint and ensure metric data is available."""
        try:
            # Fetch data for the user's selected unit system
            current_page = await self.hass.async_add_executor_job(self._fetch_data, self.url)
            response.raise_for_status()
            
            current_soup = BeautifulSoup(current_page, "html.parser")
            temp_element = current_soup.find("script", id="app-root-state")
            data={}
            try:
                json_object = json.loads(temp_element.get_text())
                for k in json_object.keys():
                    if 'b' in json_object[k] and 'summaries' in json_object[k]['b']:
                        weather_summary = json_object[k]['b']['summaries'][0]
                        if "imperial" in weather_summary:
                            if "dewptAvg" in weather_summary['imperial']:
                                data["dew_point"] = self.FtoC(weather_summary['imperial']['dewptAvg'])

                            if "windchillAvg" in weather_summary['imperial']:
                                data["apparent_temperature"] = self.FtoC(weather_summary['imperial']['windchillAvg'])

                            if "precipRate" in weather_summary['imperial']:
                                data["precipitation"] = weather_summary['imperial']['precipRate']*25.4
                                data["precipitation_unit"] = "mm"

                            if "tempAvg" in weather_summary['imperial']:
                                data["temperature"] = self.FtoC(weather_summary['imperial']['tempAvg'])
                                data["temperature_unit"] = "°C"

                            if "windspeedAvg" in weather_summary['imperial']:
                                data["wind_speed"] = weather_summary['imperial']['windspeedAvg']*1.60934
                                data["wind_speed_unit"] = "km/h"

                            if "windgustAvg" in weather_summary['imperial']:
                                data["wind_gust_speed"] = weather_summary['imperial']['windgustAvg']*1.60934

                            if "pressureMax" in weather_summary['imperial']:
                                data["pressure"] = weather_summary['imperial']['pressureMax']*33.86389

                        if 'humidityAvg' in weather_summary:
                            data["humidity"] = weather_summary['humidityAvg']

                        if 'winddirAvg' in weather_summary:
                            data["wind_bearing"] = weather_summary['winddirAvg']

                        if 'uvHigh' in weather_summary:
                            data["uv_index"] = weather_summary['uvHigh']

                        data['latest_update'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

            except ValueError as e:
                _LOGGER.error("Error fetching current weather data: %s", e)
                self._state = None # Set to unavailable on error
                return # Stop the update if the first source fails

            return data
        except requests.exceptions.RequestException as err:
            raise UpdateFailed(f"Error communicating with API: {err}")


class WUWeather(CoordinatorEntity, WeatherEntity):
    """Representation of a WU Weather entity."""

    def __init__(self, coordinator, name):
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._name = name
        # This entity does not provide forecasts from this API endpoint
        self._attr_supported_features = 0

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def native_temperature(self) -> float | None:
        """Return the temperature."""
        if self.coordinator.data:
            return self.coordinator.data.get("temperature")
        return None

    @property
    def native_temperature_unit(self) -> str:
        """Return the unit of measurement for temperature."""
        return UnitOfTemperature.CELSIUS

    @property
    def native_apparent_temperature(self) -> float | None:
        """Return the apparent temperature (feels like)."""
        if self.coordinator.data:
            return self.coordinator.data.get("apparent_temperature")
        return None

    @property
    def native_pressure(self) -> float | None:
        """Return the pressure."""
        if self.coordinator.data:
            return self.coordinator.data.get("pressure")
        return None

    @property
    def native_pressure_unit(self) -> str:
        """Return the unit of measurement for pressure."""
        return UnitOfPressure.HPA

    @property
    def humidity(self) -> float | None:
        """Return the humidity."""
        if self.coordinator.data:
            return self.coordinator.data.get("humidity")
        return None

    @property
    def native_wind_speed(self) -> float | None:
        """Return the wind speed."""
        if self.coordinator.data:
            return self.coordinator.data.get("wind_speed")
        return None
    
    @property
    def native_wind_speed_unit(self) -> str:
        return UnitOfSpeed.KILOMETERS_PER_HOUR

    @property
    def wind_bearing(self) -> float | None:
        """Return the wind bearing."""
        if self.coordinator.data:
            return self.coordinator.data.get("wind_bearing")
        return None

    @property
    def uv_index(self) -> float | None:
        """Return the UV index."""
        if self.coordinator.data:
            return self.coordinator.data.get("uv_index")
        return None

    @property
    def native_wind_gust_speed(self) -> float | None:
        """Return the wind gust speed."""
        if self.coordinator.data:
            return self.coordinator.data.get("wind_gust_speed")
        return None
    
    @property
    def native_total_precipitation(self) -> float | None:
        """Return the total precipitation."""
        if self.coordinator.data:
            return self.coordinator.data.get("precipitation")
        return None

    @property
    def native_precipitation_unit(self) -> str:
        """Return the unit of measurement for precipitation."""
        return UnitOfLength.MILLIMETERS