import requests
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def travel_assistant_page(request):
    return render(request, "travel_assistant/travel_assistant.html")


def get_weather(destination, travel_date):
    try:
        # Find destination coordinates
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {
            "name": destination,
            "count": 1,
            "language": "en",
            "format": "json",
        }

        geo_response = requests.get(
            geo_url,
            params=geo_params,
            timeout=10
        )
        geo_data = geo_response.json()

        if not geo_data.get("results"):
            return None

        place = geo_data["results"][0]

        latitude = place["latitude"]
        longitude = place["longitude"]

        location_name = place.get("name", destination)
        country = place.get("country", "")

        # Get weather for selected date
        weather_url = "https://api.open-meteo.com/v1/forecast"

        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": (
                "weather_code,"
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_probability_max,"
                "precipitation_sum,"
                "wind_speed_10m_max"
            ),
            "timezone": "auto",
            "start_date": travel_date,
            "end_date": travel_date,
        }

        weather_response = requests.get(
            weather_url,
            params=weather_params,
            timeout=10
        )

        weather_data = weather_response.json()

        daily = weather_data.get("daily")

        if not daily or not daily.get("time"):
            return None

        code = daily["weather_code"][0]
        temp_max = daily["temperature_2m_max"][0]
        temp_min = daily["temperature_2m_min"][0]
        rain_probability = daily["precipitation_probability_max"][0]
        rain_amount = daily["precipitation_sum"][0]
        wind_speed = daily["wind_speed_10m_max"][0]

        condition_map = {
            0: "Clear Sky",
            1: "Mainly Clear",
            2: "Partly Cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Foggy",
            51: "Light Drizzle",
            53: "Moderate Drizzle",
            55: "Heavy Drizzle",
            61: "Light Rain",
            63: "Moderate Rain",
            65: "Heavy Rain",
            71: "Light Snow",
            73: "Moderate Snow",
            75: "Heavy Snow",
            80: "Rain Showers",
            81: "Moderate Rain Showers",
            82: "Heavy Rain Showers",
            95: "Thunderstorm",
            96: "Thunderstorm with Hail",
            99: "Severe Thunderstorm",
        }

        condition = condition_map.get(code, "Variable Weather")

        # Travel suitability
        if code in [95, 96, 99] or wind_speed >= 45:
            travel_status = "Not Recommended"
            travel_class = "danger"
            recommendation = (
                "Severe weather conditions are possible. "
                "Consider postponing the trip or making alternative arrangements."
            )

        elif rain_probability >= 70 or rain_amount >= 15:
            travel_status = "Use Caution"
            travel_class = "warning"
            recommendation = (
                "Rain is likely during your trip. "
                "Carry an umbrella or rain protection and plan your journey carefully."
            )

        elif temp_max >= 38:
            travel_status = "Use Caution"
            travel_class = "warning"
            recommendation = (
                "Very high temperatures are expected. "
                "Carry sufficient water, sunscreen and light clothing."
            )

        else:
            travel_status = "Good to Travel"
            travel_class = "good"
            recommendation = (
                "Weather conditions look generally favorable for travel. "
                "Have a safe and enjoyable journey."
            )

        # Smart packing suggestions
        packing = []

        if rain_probability >= 40 or rain_amount > 0:
            packing.append("Umbrella / Raincoat")

        if temp_max >= 30:
            packing.append("Light Cotton Clothes")
            packing.append("Sunscreen")

        if temp_max >= 35:
            packing.append("Water Bottle")

        if temp_min <= 15:
            packing.append("Warm Clothing")

        if wind_speed >= 30:
            packing.append("Windproof Jacket")

        if not packing:
            packing.append("Comfortable Travel Clothes")

        return {
            "location": f"{location_name}, {country}".strip(", "),
            "date": travel_date,
            "condition": condition,
            "temperature_max": temp_max,
            "temperature_min": temp_min,
            "rain_probability": rain_probability,
            "rain_amount": rain_amount,
            "wind_speed": wind_speed,
            "travel_status": travel_status,
            "travel_class": travel_class,
            "recommendation": recommendation,
            "packing": packing,
        }

    except requests.RequestException:
        return None

    except Exception:
        return None


@login_required
def travel_assistant_api(request):

    if request.method == "POST":
        destination = request.POST.get(
            "destination",
            ""
        ).strip()

        travel_date = request.POST.get(
            "travel_date",
            ""
        ).strip()

    else:
        destination = request.GET.get(
            "destination",
            ""
        ).strip()

        travel_date = request.GET.get(
            "travel_date",
            ""
        ).strip()

    if not destination:
        return JsonResponse({
            "success": False,
            "message": "Please enter a travel destination."
        })

    if not travel_date:
        return JsonResponse({
            "success": False,
            "message": "Please select a travel date."
        })

    try:
        selected_date = datetime.strptime(
            travel_date,
            "%Y-%m-%d"
        ).date()

        today = datetime.now().date()

        if selected_date < today:
            return JsonResponse({
                "success": False,
                "message": "Please select today or a future travel date."
            })

    except ValueError:
        return JsonResponse({
            "success": False,
            "message": "Please enter a valid travel date."
        })

    result = get_weather(
        destination,
        travel_date
    )

    if not result:
        return JsonResponse({
            "success": False,
            "message": (
                "I couldn't find weather information "
                "for that destination. Please check the place name."
            )
        })

    return JsonResponse({
        "success": True,
        "data": result
    })