import requests
from django.conf import settings


def get_weatherapi(city):
    api_key = settings.WEATHERAPI_KEY

    if not api_key:
        return {
            "success": False,
            "error": "WeatherAPI key is not configured."
        }

    url = "https://api.weatherapi.com/v1/current.json"

    params = {
        "key": api_key,
        "q": city,
        "aqi": "no"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        data = response.json()

        if response.status_code != 200:
            return {
                "success": False,
                "error": data.get(
                    "error",
                    {}
                ).get(
                    "message",
                    "Unable to fetch WeatherAPI data."
                )
            }

        current = data.get("current", {})
        location = data.get("location", {})
        condition = current.get("condition", {})

        return {
            "success": True,
            "city": location.get("name", city),
            "country": location.get("country", ""),
            "temperature": current.get("temp_c"),
            "feels_like": current.get("feelslike_c"),
            "humidity": current.get("humidity"),
            "wind_speed": current.get("wind_kph"),
            "pressure": current.get("pressure_mb"),
            "condition": condition.get(
                "text",
                "Unknown"
            ),
            "visibility": current.get("vis_km"),
        }

    except requests.RequestException:
        return {
            "success": False,
            "error": "WeatherAPI service is unavailable."
        }