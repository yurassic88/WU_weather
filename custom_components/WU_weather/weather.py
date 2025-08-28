"""Platform for weather integration."""
from __future__ import annotations
import logging
from datetime import timedelta, datetime
import json

import voluptuous as vol
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

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
from homeassistant.exceptions import ConfigEntryNotReady
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
    
    try:
        # Manually trigger the first refresh to handle potential startup errors
        await coordinator.async_config_entry_first_refresh()
    except UpdateFailed as err:
        # If the first refresh fails, we raise this special exception
        # to let Home Assistant know it should retry later.
        raise ConfigEntryNotReady from err

    async_add_entities([WUWeather(coordinator, name)])


class WeatherUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching WU data."""

    def __init__(self, hass, current_weather_url):
        """Initialize."""
        self.url = current_weather_url
        self.api_key = ""

        super().__init__(
            hass,
            _LOGGER,
            name="WU Weather",
            update_interval=SCAN_INTERVAL,
        )

    def FtoC(self, fahrenheit):
        """Convert Fahrenheit to Celsius."""
        return (fahrenheit - 32) * 5.0/9.0

    def _fetch_data(self):
        """Fetch data from a URL in a blocking way."""
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
    
    def _fetch_data_with_api(self):
        """Fetch data from a URL in a blocking way."""
        try:
            response = requests.get(f"https://api.weather.com/v2/pws/observations/current?apiKey={self.api_key}&stationId=IAMSTE256&numericPrecision=decimal&format=json&units=m", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def _async_update_data(self):
        """Fetch data from API endpoint and parse it."""
        try:
            # Fetch data for the user's selected unit system
            current_page = await self.hass.async_add_executor_job(self._fetch_data)
            
            current_soup = BeautifulSoup(current_page, "html.parser")
            temp_element = current_soup.find("script", id="app-root-state")
            data={}
            api_key = ""
            try:
                json_object = json.loads(temp_element.get_text())
                for k in json_object.keys():
                    if('u' in json_object[k]):
                        api_key = parse_qs(urlparse(json_object[k]['u']).query).get("apiKey", " ")[0]
                        print(api_key)
                        break
                    
            except (ValueError, KeyError) as e:
                _LOGGER.error("Error parsing weather data: %s", e)
                raise UpdateFailed(f"Error parsing weather data: {e}")
            
            if(api_key!=""):
                self.api_key = api_key

                current_weather = await self.hass.async_add_executor_job(self._fetch_data_with_api)
                if 'observations' in current_weather and len(current_weather['observations'])>0:
                    weather_summary = current_weather['observations'][0]

                    if "metric" in weather_summary:
                        metric = weather_summary['metric']
                        if "dewpt" in metric:
                            data["dew_point"] = metric["dewpt"]

                        if "windChill" in metric:
                            data["apparent_temperature"] = metric["windChill"]

                        if "precipRate" in metric:
                            data["precipitation"] = metric["precipRate"]
                            data["precipitation_unit"] = "mm"

                        if "temp" in metric:
                            data["temperature"] = metric["temp"]
                            data["temperature_unit"] = "°C"

                        if "windSpeed" in metric:
                            data["wind_speed"] = metric["windSpeed"]
                            data["wind_speed_unit"] = "km/h"
                        
                        if "windGust" in metric:
                            data["wind_gust_speed"] = metric["windGust"]

                        if "pressure" in metric:
                            data["pressure"] = metric["pressure"]

                    if 'humidity' in weather_summary:
                        data["humidity"] = weather_summary['humidity']

                    if 'winddir' in weather_summary:
                        data["wind_bearing"] = weather_summary['winddir']

                    if 'uv' in weather_summary:
                        data["uv_index"] = weather_summary['uv']

                    data['latest_update'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

            

            return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")


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
