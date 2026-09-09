import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET


def alerts_page(request):
    return render(request, "alerts/alerts.html")


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
def alerts_api(request):

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

        # Find location
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

        # Weather data
        weather_params = urlencode({
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "daily": (
                "weather_code,"
                "precipitation_probability_max,"
                "precipitation_sum,"
                "wind_speed_10m_max,"
                "temperature_2m_max"
            ),
            "forecast_days": 3,
            "timezone": "auto"
        })

        weather_url = (
            "https://api.open-meteo.com/v1/forecast?"
            + weather_params
        )

        weather_data = get_json(weather_url)

        current = weather_data.get("current", {})
        daily = weather_data.get("daily", {})

        alerts = []

        weather_code = current.get("weather_code")
        wind = current.get("wind_speed_10m")
        temperature = current.get("temperature_2m")

        rain_probability = (
            daily.get(
                "precipitation_probability_max",
                [0]
            )[0] or 0
        )

        rainfall = (
            daily.get(
                "precipitation_sum",
                [0]
            )[0] or 0
        )

        # Heavy rain
        if rain_probability >= 70 or rainfall >= 20:

            alerts.append({
                "type": "warning",
                "icon": "🌧️",
                "title": "Heavy Rainfall",
                "message":
                    "High rainfall probability or significant "
                    "rainfall is expected."
            })

        # Thunderstorm
        if weather_code in [95, 96, 99]:

            alerts.append({
                "type": "danger",
                "icon": "⛈️",
                "title": "Thunderstorm Risk",
                "message":
                    "Thunderstorm conditions are indicated "
                    "by the current weather data."
            })

        # Strong wind
        if wind is not None and wind >= 30:

            alerts.append({
                "type": "warning",
                "icon": "💨",
                "title": "Strong Wind",
                "message":
                    "Strong wind conditions are currently "
                    "indicated."
            })

        # High temperature
        if temperature is not None and temperature >= 35:

            alerts.append({
                "type": "warning",
                "icon": "🌡️",
                "title": "High Temperature",
                "message":
                    "High temperature conditions are currently "
                    "being observed."
            })

        # No major alert
        if not alerts:

            alerts.append({
                "type": "safe",
                "icon": "✅",
                "title": "No Major Weather Alert",
                "message":
                    "No major weather condition requiring "
                    "an alert was detected from the available data."
            })

        return JsonResponse({
            "success": True,

            "location": {
                "city": city,
                "country": country
            },

            "alerts": alerts
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
            "message": "Unable to fetch weather alerts.",
            "error": str(error)
        }, status=500)