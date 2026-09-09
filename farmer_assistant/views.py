import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET


def farmer_assistant_page(request):
    return render(
        request,
        "farmer_assistant/farmer_assistant.html"
    )


def get_json(url):
    request = Request(
        url,
        headers={
            "User-Agent": "WeatherGPT/1.0",
            "Accept": "application/json"
        }
    )

    with urlopen(request, timeout=20) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


@require_GET
def farmer_weather_api(request):

    location = request.GET.get(
        "location",
        ""
    ).strip()

    if not location:
        return JsonResponse({
            "success": False,
            "message": "Please enter a location."
        }, status=400)

    try:

        # Location search
        geo_params = urlencode({
            "name": location,
            "count": 1,
            "language": "en",
            "format": "json"
        })

        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search?"
            + geo_params
        )

        geo_data = get_json(geo_url)

        results = geo_data.get(
            "results",
            []
        )

        if not results:
            return JsonResponse({
                "success": False,
                "message": "Location not found."
            }, status=404)

        place = results[0]

        latitude = place.get("latitude")
        longitude = place.get("longitude")

        city = place.get(
            "name",
            location
        )

        country = place.get(
            "country",
            ""
        )

        # Weather + forecast
        weather_params = urlencode({
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "daily": (
                "weather_code,"
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_probability_max,"
                "precipitation_sum,"
                "wind_speed_10m_max"
            ),
            "forecast_days": 7,
            "timezone": "auto"
        })

        weather_url = (
            "https://api.open-meteo.com/v1/forecast?"
            + weather_params
        )

        weather_data = get_json(
            weather_url
        )

        current = weather_data.get(
            "current",
            {}
        )

        daily = weather_data.get(
            "daily",
            {}
        )

        return JsonResponse({

            "success": True,

            "location": {
                "city": city,
                "country": country,
                "latitude": latitude,
                "longitude": longitude
            },

            "current": {
                "temperature":
                    current.get("temperature_2m"),

                "humidity":
                    current.get("relative_humidity_2m"),

                "feels_like":
                    current.get("apparent_temperature"),

                "rain":
                    current.get("precipitation"),

                "wind":
                    current.get("wind_speed_10m"),

                "condition":
                    get_weather_condition(
                        current.get("weather_code")
                    )
            },

            "forecast": {

                "dates":
                    daily.get("time", []),

                "rain_probability":
                    daily.get(
                        "precipitation_probability_max",
                        []
                    ),

                "rainfall":
                    daily.get(
                        "precipitation_sum",
                        []
                    ),

                "max_temperature":
                    daily.get(
                        "temperature_2m_max",
                        []
                    ),

                "min_temperature":
                    daily.get(
                        "temperature_2m_min",
                        []
                    ),

                "wind":
                    daily.get(
                        "wind_speed_10m_max",
                        []
                    )
            }

        })

    except HTTPError as error:

        return JsonResponse({
            "success": False,
            "message": "Weather service error.",
            "error": f"HTTP {error.code}"
        }, status=502)

    except URLError as error:

        return JsonResponse({
            "success": False,
            "message": "Unable to connect to weather service.",
            "error": str(error.reason)
        }, status=502)

    except Exception as error:

        return JsonResponse({
            "success": False,
            "message": "Unable to fetch weather data.",
            "error": str(error)
        }, status=500)


def get_weather_condition(code):

    conditions = {

        0: "Clear Sky",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Overcast",

        45: "Fog",
        48: "Rime Fog",

        51: "Light Drizzle",
        53: "Moderate Drizzle",
        55: "Dense Drizzle",

        61: "Slight Rain",
        63: "Moderate Rain",
        65: "Heavy Rain",

        71: "Slight Snow",
        73: "Moderate Snow",
        75: "Heavy Snow",

        80: "Rain Showers",
        81: "Moderate Rain Showers",
        82: "Heavy Rain Showers",

        85: "Snow Showers",
        86: "Heavy Snow Showers",

        95: "Thunderstorm",
        96: "Thunderstorm With Hail",
        99: "Heavy Thunderstorm With Hail"
    }

    return conditions.get(
        code,
        "Unknown Weather"
    )