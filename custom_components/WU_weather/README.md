# WU Weather Integration for Home Assistant

This is a simple Home Assistant integration that scrapes current weather and forecast data from Weather Underground (WU). It is designed to be a starting point and may require modification to work correctly, as it relies on web scraping.

## Features

*   Scrapes current temperature, humidity, and other conditions from a WU URL.
*   Scrapes a multi-day forecast from a WU forecast URL.
*   Configurable through the Home Assistant UI.
*   Supports legacy YAML configuration.

## Installation

The recommended way to install this integration is through the [Home Assistant Community Store (HACS)](https://hacs.xyz/).

1.  Add this repository as a custom repository in HACS.
2.  Search for "WU Weather" and install it.
3.  Restart Home Assistant.

## Configuration

1.  Go to **Settings > Devices & Services**.
2.  Click **Add Integration** and search for "WU Weather".
3.  Follow the on-screen instructions. You will be asked to provide the following:
    *   **Name:** A name for your sensor (e.g., "Home Weather").
    *   **Current Weather URL:** The Weather Underground URL for the current conditions of your location.
    *   **Forecast URL:** The Weather Underground URL for the forecast of your location.

### Finding Your URLs

1.  Go to [Weather Underground](https://www.wunderground.com/).
2.  Search for your location.
3.  Once you are on the weather page for your location, copy the URL from your browser's address bar. This is your **Current Weather URL**.
4.  On the same page, find the link to the "10-Day Forecast" (or similar) and click it.
5.  Copy the URL from the forecast page. This is your **Forecast URL**.

### Legacy YAML Configuration

You can also configure this integration by adding the following to your `configuration.yaml` file:

```yaml
sensor:
  - platform: WU_weather
    name: "WU Weather"
    current_weather_url: "YOUR_CURRENT_WEATHER_URL"
    forecast_url: "YOUR_FORECAST_URL"
```

## Sensor Data

The integration will create a sensor with the name you provided.

*   **State:** The current temperature in Celsius.
*   **Attributes:**
    *   `humidity`: The current humidity.
    *   `forecast`: A list of dictionaries, where each dictionary contains the forecast for a single day (`date`, `temp_high`, `temp_low`, `condition`).

## Important Note on Scraping

This integration works by scraping the HTML of the Weather Underground website. Websites can change their structure at any time, which will break this integration.

If the sensor stops working, you will likely need to update the `sensor.py` file (`custom_components/WU_weather/sensor.py`) with the new HTML tags and classes for the data you want to scrape.

## Disclaimer

This integration is not affiliated with Weather Underground. Web scraping may be against the terms of service of some websites. Use at your own risk.
