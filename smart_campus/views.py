from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import requests


@login_required
def smart_campus_page(request):
    return render(request, "smart_campus/smart_campus.html")


@login_required
def smart_campus_api(request):
    latitude = request.GET.get("latitude")
    longitude = request.GET.get("longitude")

    if not latitude or not longitude:
        return JsonResponse({
            "success": False,
            "error": "Campus location is required."
        })

    try:
        url = "https://api.open-meteo.com/v1/forecast"

        params = {
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
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_probability_max,"
                "precipitation_sum,"
                "wind_speed_10m_max"
            ),
            "forecast_days": 3,
            "timezone": "auto"
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200:
            return JsonResponse({
                "success": False,
                "error": "Weather service unavailable."
            })

        current = data.get("current", {})
        daily = data.get("daily", {})

        temperature = current.get("temperature_2m")
        rain_probability = (
            daily.get("precipitation_probability_max", [0])[0]
        )
        wind_speed = current.get("wind_speed_10m")
        precipitation = current.get("precipitation", 0)

        # Smart campus recommendations
        recommendations = []

        if rain_probability >= 60 or precipitation > 0:
            recommendations.append(
                "Carry an umbrella and plan outdoor activities carefully."
            )

        if wind_speed and wind_speed >= 30:
            recommendations.append(
                "Avoid outdoor events because of strong winds."
            )

        if temperature is not None and temperature >= 35:
            recommendations.append(
                "High temperature expected. Stay hydrated and avoid prolonged outdoor exposure."
            )

        if not recommendations:
            recommendations.append(
                "Weather conditions are suitable for normal campus activities."
            )

        return JsonResponse({
            "success": True,
            "temperature": temperature,
            "humidity": current.get("relative_humidity_2m"),
            "feels_like": current.get("apparent_temperature"),
            "precipitation": precipitation,
            "rain_probability": rain_probability,
            "wind_speed": wind_speed,
            "recommendations": recommendations,
            "forecast": {
                "max_temperature": daily.get("temperature_2m_max", []),
                "min_temperature": daily.get("temperature_2m_min", []),
                "rain_probability": daily.get(
                    "precipitation_probability_max", []
                )
            }
        })

    except requests.RequestException:
        return JsonResponse({
            "success": False,
            "error": "Unable to connect to weather service."
        })