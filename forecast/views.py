import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET


def forecast_page(request):
    return render(request, "forecast/forecast.html")


def get_json(url):
    request = Request(
        url,
        headers={
            "User-Agent": "WeatherGPT/1.0",
            "Accept": "application/json"
        }
    )

    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


@require_GET
def forecast_api(request):

    location = request.GET.get("location", "").strip()

    if not location:
        return JsonResponse({
            "success": False,
            "message": "Please enter a city or location."
        }, status=400)

    try:

        # -----------------------------------------
        # STEP 1: LOCATION → COORDINATES
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

        # -----------------------------------------
        # STEP 2: 7-DAY FORECAST
        # -----------------------------------------

        forecast_params = urlencode({
            "latitude": latitude,
            "longitude": longitude,
            "daily": (
                "weather_code,"
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_probability_max,"
                "wind_speed_10m_max"
            ),
            "timezone": "auto",
            "forecast_days": 7
        })

        forecast_url = (
            "https://api.open-meteo.com/v1/forecast?"
            + forecast_params
        )

        forecast_data = get_json(forecast_url)
        daily = forecast_data.get("daily", {})

        dates = daily.get("time", [])
        codes = daily.get("weather_code", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        rain = daily.get("precipitation_probability_max", [])
        winds = daily.get("wind_speed_10m_max", [])

        forecast = []

        for i in range(len(dates)):
            forecast.append({
                "date": dates[i],
                "weather_code": codes[i] if i < len(codes) else None,
                "condition": get_weather_condition(
                    codes[i] if i < len(codes) else None
                ),
                "max_temperature": (
                    max_temps[i] if i < len(max_temps) else None
                ),
                "min_temperature": (
                    min_temps[i] if i < len(min_temps) else None
                ),
                "rain_probability": (
                    rain[i] if i < len(rain) else None
                ),
                "wind_speed": (
                    winds[i] if i < len(winds) else None
                )
            })

        return JsonResponse({
            "success": True,
            "location": {
                "city": city,
                "country": country,
                "latitude": latitude,
                "longitude": longitude
            },
            "forecast": forecast,
            "units": {
                "temperature": "°C",
                "wind_speed": "km/h",
                "rain_probability": "%"
            }
        })

    except HTTPError as error:

        return JsonResponse({
            "success": False,
            "message": "Forecast service returned an error.",
            "error": f"HTTP {error.code}"
        }, status=502)

    except URLError as error:

        return JsonResponse({
            "success": False,
            "message": "Unable to connect to forecast service.",
            "error": str(error.reason)
        }, status=502)

    except Exception as error:

        return JsonResponse({
            "success": False,
            "message": "Unable to fetch forecast data.",
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

    return conditions.get(code, "Unknown Weather")