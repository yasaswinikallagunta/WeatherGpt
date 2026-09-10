import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .openweather import get_openweather
from .weatherapi import get_weatherapi


def weather_page(request):
    return render(request, "weather/weather.html")


def get_json(url):
    request = Request(
        url,
        headers={
            "User-Agent": "WeatherGPT/1.0",
            "Accept": "application/json"
        }
    )

    with urlopen(request, timeout=20) as response:
        data = response.read().decode("utf-8")
        return json.loads(data)


@require_GET
def weather_api(request):

    location = request.GET.get("location", "").strip()

    if not location:
        return JsonResponse({
            "success": False,
            "message": "Please enter a city or location."
        }, status=400)

    try:

        # -----------------------------------------
        # STEP 1: LOCATION SEARCH
        # -----------------------------------------

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

        results = geo_data.get("results", [])

        if not results:
            return JsonResponse({
                "success": False,
                "message": "Location not found."
            }, status=404)

        place = results[0]

        latitude = place.get("latitude")
        longitude = place.get("longitude")

        city = place.get("name", location)
        country = place.get("country", "")

        if latitude is None or longitude is None:
            return JsonResponse({
                "success": False,
                "message": "Location coordinates not available."
            }, status=500)

        # -----------------------------------------
        # STEP 2: CURRENT WEATHER
        # -----------------------------------------

        weather_params = urlencode({
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "timezone": "auto"
        })

        weather_url = (
            "https://api.open-meteo.com/v1/forecast?"
            + weather_params
        )

        weather_data = get_json(weather_url)

        current = weather_data.get("current", {})

        if not current:
            return JsonResponse({
                "success": False,
                "message": "Current weather data is unavailable."
            }, status=500)

        # -----------------------------------------
        # STEP 3: WEATHER CONDITION
        # -----------------------------------------

        weather_code = current.get("weather_code")

        condition = get_weather_condition(weather_code)

        # -----------------------------------------
        # STEP 4: RESPONSE
        # -----------------------------------------

        response_data = {
            "success": True,

            "location": {
                "city": city,
                "country": country,
                "latitude": latitude,
                "longitude": longitude
            },

            "weather": {
                "temperature": current.get("temperature_2m"),
                "humidity": current.get(
                    "relative_humidity_2m"
                ),
                "feels_like": current.get(
                    "apparent_temperature"
                ),
                "wind_speed": current.get(
                    "wind_speed_10m"
                ),
                "weather_code": weather_code,
                "condition": condition
            },

            "units": {
                "temperature": "°C",
                "wind_speed": "km/h"
            }
        }

        return JsonResponse(response_data)

    except HTTPError as error:

        return JsonResponse({
            "success": False,
            "message": "Weather service returned an error.",
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
        48: "Depositing Rime Fog",

        51: "Light Drizzle",
        53: "Moderate Drizzle",
        55: "Dense Drizzle",

        56: "Light Freezing Drizzle",
        57: "Dense Freezing Drizzle",

        61: "Slight Rain",
        63: "Moderate Rain",
        65: "Heavy Rain",

        66: "Light Freezing Rain",
        67: "Heavy Freezing Rain",

        71: "Slight Snow",
        73: "Moderate Snow",
        75: "Heavy Snow",

        77: "Snow Grains",

        80: "Slight Rain Showers",
        81: "Moderate Rain Showers",
        82: "Violent Rain Showers",

        85: "Slight Snow Showers",
        86: "Heavy Snow Showers",

        95: "Thunderstorm",
        96: "Thunderstorm With Slight Hail",
        99: "Thunderstorm With Heavy Hail"
    }

    return conditions.get(
        code,
        "Unknown Weather"
    )
def openweather_test(request):
    city = request.GET.get("city", "Ongole").strip()

    data = get_openweather(city)

    return JsonResponse(data)
def weatherapi_test(request):
    city = request.GET.get("city", "").strip()

    if not city:
        city = "Ongole"

    data = get_weatherapi(city)

    return JsonResponse(data)