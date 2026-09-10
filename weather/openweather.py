import requests
from django.conf import settings


def get_openweather(city):
    api_key = settings.OPENWEATHER_API_KEY

    if not api_key:
        return {
            "success": False,
            "error": "OpenWeather API key is not configured."
        }

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            return {
                "success": False,
                "error": "Unable to fetch OpenWeather data."
            }

        data = response.json()

        return {
            "success": True,
            "city": data.get("name", city),
            "country": data.get("sys", {}).get("country", ""),
            "temperature": data.get("main", {}).get("temp"),
            "feels_like": data.get("main", {}).get("feels_like"),
            "humidity": data.get("main", {}).get("humidity"),
            "pressure": data.get("main", {}).get("pressure"),
            "wind_speed": data.get("wind", {}).get("speed"),
            "condition": data.get("weather", [{}])[0].get("description", "Unknown"),
            "weather_main": data.get("weather", [{}])[0].get("main", "Unknown"),
        }

    except requests.RequestException:
        return {
            "success": False,
            "error": "OpenWeather service is temporarily unavailable."
        }