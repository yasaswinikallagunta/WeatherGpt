from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import ChatHistory, RecentSearch

import requests
import re


# =========================================================
# WEATHER CONDITIONS
# =========================================================

def get_condition(code):

    conditions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",

        45: "Foggy",
        48: "Foggy",

        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Heavy drizzle",

        61: "Light rain",
        63: "Moderate rain",
        65: "Heavy rain",

        71: "Light snowfall",
        73: "Moderate snowfall",
        75: "Heavy snowfall",

        80: "Rain showers",
        81: "Moderate rain showers",
        82: "Heavy rain showers",

        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Severe thunderstorm",
    }

    return conditions.get(
        code,
        "Unknown weather"
    )


# =========================================================
# GET WEATHER DATA FOR ANY LOCATION
# =========================================================

def get_weather(location):

    try:

        geo_response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": location,
                "count": 10,
                "language": "en",
                "format": "json",
            },
            timeout=10,
        )

        geo_response.raise_for_status()

        geo_data = geo_response.json()

        results = geo_data.get(
            "results",
            []
        )

        if not results:
            return None


        place = results[0]


        weather_response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],

                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m"
                ),

                "hourly": (
                    "temperature_2m,"
                    "precipitation_probability,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m"
                ),

                "daily": (
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "precipitation_probability_max,"
                    "precipitation_sum,"
                    "weather_code,"
                    "wind_speed_10m_max"
                ),

                "forecast_days": 7,
                "timezone": "auto",
            },

            timeout=10,
        )

        weather_response.raise_for_status()

        data = weather_response.json()


        current = data.get(
            "current",
            {}
        )

        hourly = data.get(
            "hourly",
            {}
        )

        daily = data.get(
            "daily",
            {}
        )


        return {

            "city":
                place.get(
                    "name",
                    location
                ),

            "state":
                place.get(
                    "admin1",
                    ""
                ),

            "district":
                place.get(
                    "admin2",
                    ""
                ),

            "country":
                place.get(
                    "country",
                    ""
                ),

            "latitude":
                place.get(
                    "latitude"
                ),

            "longitude":
                place.get(
                    "longitude"
                ),

            "temperature":
                current.get(
                    "temperature_2m"
                ),

            "humidity":
                current.get(
                    "relative_humidity_2m"
                ),

            "feels_like":
                current.get(
                    "apparent_temperature"
                ),

            "rain":
                current.get(
                    "precipitation"
                ),

            "wind":
                current.get(
                    "wind_speed_10m"
                ),

            "weather_code":
                current.get(
                    "weather_code"
                ),

            "condition":
                get_condition(
                    current.get(
                        "weather_code"
                    )
                ),

            "hourly":
                hourly,

            "daily":
                daily,
        }


    except Exception:

        return None


# =========================================================
# SAVE CHAT
# =========================================================

def save_chat(
    user,
    message,
    reply,
    location=""
):

    ChatHistory.objects.create(

        user=user,

        message=message,

        response=reply,

        location=location
    )
    # =========================================================
# BUILD LOCATION NAME
# =========================================================

def build_location_name(weather):

    parts = []

    city = weather.get("city", "")
    district = weather.get("district", "")
    state = weather.get("state", "")

    if city:
        parts.append(city)

    if district and district.lower() != city.lower():
        parts.append(district)

    if state and state.lower() not in [
        part.lower() for part in parts
    ]:
        parts.append(state)

    return ", ".join(parts)


# =========================================================
# EXTRACT LOCATION FROM NATURAL LANGUAGE
# =========================================================

def detect_location(message):

    text = message.strip()

    patterns = [
        r"\bweather\s+(?:in|at|for|of|near)\s+(.+)",
        r"\btemperature\s+(?:in|at|for|of|near)\s+(.+)",
        r"\btemp\s+(?:in|at|for|of|near)\s+(.+)",
        r"\bforecast\s+(?:in|at|for|of|near)\s+(.+)",
        r"\brain(?:fall|ing)?\s+(?:in|at|for|of|near)\s+(.+)",
        r"\bprecipitation\s+(?:in|at|for|of|near)\s+(.+)",
        r"\bwind\s+(?:in|at|for|of|near)\s+(.+)",
        r"\bhumidity\s+(?:in|at|for|of|near)\s+(.+)",
        r"\bclimate\s+(?:in|at|for|of|near)\s+(.+)",
        r"\balerts?\s+(?:in|at|for|of|near)\s+(.+)",
        r"\bwarning\s+(?:in|at|for|of|near)\s+(.+)",
        r"\bconditions?\s+(?:in|at|for|of|near)\s+(.+)",
        r"\bsunny\s+(?:in|at|for|near)\s+(.+)",
        r"\bsun\s+(?:in|at|for|near)\s+(.+)",
        r"\bhot\s+(?:in|at|for|near)\s+(.+)",
        r"\bcold\s+(?:in|at|for|near)\s+(.+)",
        r"\bsafe\s+(?:in|at|for|near)\s+(.+)",
        r"\bsafety\s+(?:in|at|for|near)\s+(.+)",
    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if not match:
            continue


        location = match.group(1).strip()


        # Remove common question endings

        location = re.sub(
            r"\s+(?:today|tomorrow|tonight)$",
            "",
            location,
            flags=re.IGNORECASE
        )


        # Remove punctuation

        location = re.sub(
            r"[?.!,]+$",
            "",
            location
        ).strip()


        if location:
            return location


    return ""


# =========================================================
# DETECT WEATHER INTENT
# =========================================================

def detect_intent(question):

    q = question.lower().strip()


    # SAFETY / PRECAUTION

    if any(
        word in q
        for word in [
            "how to be safe",
            "how can i be safe",
            "how should i stay safe",
            "stay safe",
            "weather safety",
            "safety",
            "precaution",
            "precautions",
            "what should i do",
            "what can i do",
        ]
    ):
        return "safety"


    # FORECAST

    if any(
        word in q
        for word in [
            "forecast",
            "tomorrow",
            "next day",
            "coming days",
            "next week",
            "7 day",
            "7-day",
            "weekly",
        ]
    ):
        return "forecast"


    # RAIN

    if any(
        word in q
        for word in [
            "rain",
            "rainfall",
            "raining",
            "precipitation",
            "umbrella",
        ]
    ):
        return "rain"


    # WIND

    if any(
        word in q
        for word in [
            "wind",
            "winds",
            "wind speed",
            "breeze",
        ]
    ):
        return "wind"


    # ALERTS

    if any(
        word in q
        for word in [
            "alert",
            "alerts",
            "warning",
            "danger",
            "storm",
            "thunderstorm",
            "severe",
        ]
    ):
        return "alert"


    # SUNNY / CLEAR

    if any(
        word in q
        for word in [
            "sunny",
            "sun",
            "clear sky",
            "clear weather",
        ]
    ):
        return "sunny"


    # TEMPERATURE

    if any(
        word in q
        for word in [
            "temperature",
            "temp",
            "hot",
            "cold",
            "heat",
        ]
    ):
        return "temperature"


    # HUMIDITY / CLIMATE

    if any(
        word in q
        for word in [
            "humidity",
            "climate",
            "climatic",
        ]
    ):
        return "climate"


    # GENERAL WEATHER

    return "weather"


# =========================================================
# WEATHER QUESTION CHECK
# =========================================================

def is_weather_question(question):

    q = question.lower()


    weather_words = [

        "weather",
        "temperature",
        "temp",

        "rain",
        "rainfall",
        "raining",
        "precipitation",

        "forecast",
        "today",
        "tomorrow",
        "tonight",

        "wind",
        "winds",
        "breeze",

        "humidity",

        "climate",

        "sunny",
        "sun",
        "clear sky",

        "cloudy",
        "cloud",

        "storm",
        "thunderstorm",

        "alert",
        "alerts",
        "warning",

        "safe",
        "safety",
        "precaution",

        "hot",
        "cold",
        "heat",

        "condition",
        "conditions",
    ]


    return any(
        word in q
        for word in weather_words
    )
# =========================================================
# WEATHER ANSWER GENERATOR
# =========================================================

def weather_reply(weather, intent):

    location_name = build_location_name(weather)

    temperature = weather.get("temperature")
    humidity = weather.get("humidity")
    feels_like = weather.get("feels_like")
    rain = weather.get("rain")
    wind = weather.get("wind")

    condition = weather.get("condition")
    weather_code = weather.get("weather_code")

    daily = weather.get("daily", {})


    # =====================================================
    # WIND
    # =====================================================

    if intent == "wind":

        if wind is None:

            return (
                f"I couldn't get the current wind "
                f"information for <b>{location_name}</b>."
            )


        if wind < 10:

            description = (
                "The wind is light right now."
            )

        elif wind < 20:

            description = (
                "There is a gentle to moderate breeze."
            )

        elif wind < 30:

            description = (
                "The wind is fairly noticeable at the moment."
            )

        else:

            description = (
                "The wind is strong, so extra care is advisable "
                "in exposed areas."
            )


        return (
            f"💨 <b>Wind in {location_name}</b><br><br>"
            f"The current wind speed is "
            f"<b>{wind} km/h</b>. "
            f"{description}"
        )


    # =====================================================
    # RAIN
    # =====================================================

    if intent == "rain":

        probabilities = daily.get(
            "precipitation_probability_max",
            []
        )

        probability = (
            probabilities[0]
            if probabilities
            else 0
        )


        if probability >= 70:

            rain_message = (
                "There is a high chance of rain today. "
                "Carrying an umbrella would be a good idea."
            )

        elif probability >= 40:

            rain_message = (
                "There is a moderate chance of rain today."
            )

        else:

            rain_message = (
                "The chance of rain is relatively low today."
            )


        current_rain = (
            rain
            if rain is not None
            else 0
        )


        return (
            f"🌧️ <b>Rain in {location_name}</b><br><br>"
            f"Current precipitation is "
            f"<b>{current_rain} mm</b>, and today's "
            f"maximum rain probability is "
            f"<b>{probability}%</b>.<br><br>"
            f"{rain_message}"
        )


    # =====================================================
    # SUNNY / CLEAR
    # =====================================================

    if intent == "sunny":

        if weather_code in [0, 1]:

            return (
                f"☀️ <b>{location_name}</b> is currently "
                f"<b>{condition}</b>.<br><br>"
                f"Yes, the current conditions are clear "
                f"and suitable to describe as sunny."
            )


        if weather_code == 2:

            return (
                f"🌤️ <b>{location_name}</b> is currently "
                f"<b>partly cloudy</b>.<br><br>"
                f"There are some clear periods, but the sky "
                f"is not completely clear right now."
            )


        return (
            f"☁️ <b>{location_name}</b> is currently "
            f"<b>{condition}</b>.<br><br>"
            f"So it is not completely sunny at the moment."
        )


    # =====================================================
    # TEMPERATURE
    # =====================================================

    if intent == "temperature":

        return (
            f"🌡️ <b>Temperature in {location_name}</b><br><br>"
            f"The current temperature is "
            f"<b>{temperature}°C</b> and it feels like "
            f"<b>{feels_like}°C</b>.<br><br>"
            f"The current condition is "
            f"<b>{condition}</b>."
        )


    # =====================================================
    # FORECAST
    # =====================================================

    if intent == "forecast":

        dates = daily.get(
            "time",
            []
        )

        max_temps = daily.get(
            "temperature_2m_max",
            []
        )

        min_temps = daily.get(
            "temperature_2m_min",
            []
        )

        probabilities = daily.get(
            "precipitation_probability_max",
            []
        )

        codes = daily.get(
            "weather_code",
            []
        )


        reply = (
            f"📅 <b>7-Day Forecast for "
            f"{location_name}</b><br><br>"
        )


        for i in range(
            min(7, len(dates))
        ):

            minimum = (
                min_temps[i]
                if i < len(min_temps)
                else "-"
            )

            maximum = (
                max_temps[i]
                if i < len(max_temps)
                else "-"
            )

            probability = (
                probabilities[i]
                if i < len(probabilities)
                else 0
            )

            code = (
                codes[i]
                if i < len(codes)
                else None
            )

            day_condition = get_condition(
                code
            )


            reply += (
                f"📆 <b>{dates[i]}</b> — "
                f"{day_condition}<br>"
                f"🌡️ {minimum}°C – {maximum}°C<br>"
                f"🌧️ Rain probability: "
                f"{probability}%"
                f"<br><br>"
            )


        return reply


    # =====================================================
    # WEATHER ALERTS
    # =====================================================

    if intent == "alert":

        alerts = []


        if weather_code in [95, 96, 99]:

            alerts.append(
                "Thunderstorm conditions are currently detected."
            )


        if (
            rain is not None
            and rain >= 20
        ):

            alerts.append(
                "Heavy rainfall conditions are currently detected."
            )


        if (
            wind is not None
            and wind >= 30
        ):

            alerts.append(
                "Strong wind conditions are currently detected."
            )


        if (
            temperature is not None
            and temperature >= 35
        ):

            alerts.append(
                "High temperature conditions are currently detected."
            )


        if not alerts:

            return (
                f"⚠️ <b>Weather alert status for "
                f"{location_name}</b><br><br>"
                f"No major weather alerts are currently "
                f"detected from the available weather data."
            )


        return (
            f"⚠️ <b>Weather alerts for "
            f"{location_name}</b><br><br>"
            + "<br>".join(alerts)
        )


    # =====================================================
    # WEATHER SAFETY
    # =====================================================

    if intent == "safety":

        advice = []


        if weather_code in [95, 96, 99]:

            advice.append(
                "Stay indoors if possible during thunderstorms "
                "and avoid open areas."
            )


        if rain is not None and rain >= 20:

            advice.append(
                "Heavy rain may reduce visibility and make roads "
                "slippery, so travel carefully."
            )


        if wind is not None and wind >= 30:

            advice.append(
                "Strong winds can make outdoor conditions unsafe; "
                "avoid exposed areas and loose objects."
            )


        if temperature is not None and temperature >= 35:

            advice.append(
                "High temperatures can cause heat stress. "
                "Stay hydrated and avoid prolonged exposure "
                "to direct sunlight."
            )


        if not advice:

            advice.append(
                "No major weather hazard is currently detected. "
                "Normal precautions should be sufficient."
            )


        return (
            f"🛡️ <b>Weather safety for "
            f"{location_name}</b><br><br>"
            + " ".join(advice)
        )


    # =====================================================
    # CLIMATE / HUMIDITY
    # =====================================================

    if intent == "climate":

        return (
            f"🌍 <b>Atmospheric conditions in "
            f"{location_name}</b><br><br>"
            f"The current temperature is "
            f"<b>{temperature}°C</b>, humidity is "
            f"<b>{humidity}%</b>, and wind speed is "
            f"<b>{wind} km/h</b>.<br><br>"
            f"The current condition is "
            f"<b>{condition}</b>."
        )


    # =====================================================
    # GENERAL WEATHER
    # =====================================================

    return (
        f"🌦️ <b>Current weather in "
        f"{location_name}</b><br><br>"
        f"It is currently <b>{condition}</b>, "
        f"with a temperature of "
        f"<b>{temperature}°C</b>. "
        f"It feels like <b>{feels_like}°C</b>, "
        f"humidity is <b>{humidity}%</b>, "
        f"wind speed is <b>{wind} km/h</b>, "
        f"and current precipitation is "
        f"<b>{rain} mm</b>."
    )
# =========================================================
# NATURAL CONVERSATION
# =========================================================

def conversational_response(message):

    q = message.strip().lower()


    if q in [
        "hi",
        "hii",
        "hiii",
        "hello",
        "hey",
        "heyy"
    ]:

        return (
            "Hi! 👋 I'm WeatherGPT. "
            "What would you like to know about the weather?"
        )


    if "good morning" in q:

        return (
            "Good morning! ☀️ "
            "How can I help you with the weather today?"
        )


    if "good afternoon" in q:

        return (
            "Good afternoon! 🌤️ "
            "What would you like to know about the weather?"
        )


    if "good evening" in q:

        return (
            "Good evening! 🌆 "
            "How can I help you today?"
        )


    if "good night" in q:

        return (
            "Good night! 🌙 "
            "Have a peaceful night!"
        )


    if (
        "how are you" in q
        or "how r you" in q
        or "how are u" in q
    ):

        return (
            "I'm doing well! 😊 "
            "I'm ready to help you with weather information."
        )


    if (
        "who are you" in q
        or "what are you" in q
    ):

        return (
            "I'm WeatherGPT 🌦️, a conversational weather "
            "assistant. I can understand natural-language "
            "questions and provide weather, forecast, "
            "rain, wind, alert and climate information."
        )


    if (
        "what can you do" in q
        or "what do you do" in q
        or "your features" in q
    ):

        return (
            "I can help with current weather, temperature, "
            "rainfall, wind, forecasts, weather alerts and "
            "climate information. 🌦️"
        )


    if (
        "thank you" in q
        or "thanks" in q
        or q == "thank"
    ):

        return (
            "You're very welcome! 😊"
        )


    if (
        q == "sorry"
        or "i am sorry" in q
        or "i'm sorry" in q
    ):

        return (
            "That's completely okay! 😊"
        )


    if (
        q == "ok"
        or q == "okay"
        or q == "sure"
    ):

        return (
            "Sure! 😊"
        )


    if (
        q == "bye"
        or q == "goodbye"
        or q == "see you"
    ):

        return (
            "Goodbye! 👋 Have a great day!"
        )


    return None


# =========================================================
# CHATBOT PAGE
# =========================================================

@login_required(login_url="login")
def chatbot_page(request):

    searches = (
        RecentSearch.objects
        .filter(
            user=request.user
        )
        .order_by(
            "-created_at"
        )[:10]
    )


    return render(
        request,
        "chatbot/chatbot.html",
        {
            "searches": searches
        }
    )
# =========================================================
# CHATBOT API
# =========================================================

@login_required(login_url="login")
def chatbot_api(request):

    message = request.GET.get(
        "message",
        ""
    ).strip()


    # -----------------------------------------------------
    # EMPTY MESSAGE
    # -----------------------------------------------------

    if not message:

        return JsonResponse({

            "success": False,

            "reply":
                "Please enter a question."

        })


    # -----------------------------------------------------
    # PREVIOUS QUESTION WAITING FOR LOCATION
    # -----------------------------------------------------

    pending_question = request.session.get(
        "pending_weather_question"
    )

    pending_intent = request.session.get(
        "pending_weather_intent"
    )


    if pending_question:

        location = message.strip()

        weather = get_weather(
            location
        )


        if weather is not None:

            intent = (
                pending_intent
                or detect_intent(
                    pending_question
                )
            )


            reply = weather_reply(
                weather,
                intent
            )


            location_name = build_location_name(
                weather
            )


            save_chat(
                request.user,
                pending_question,
                reply,
                location_name
            )


            RecentSearch.objects.create(

                user=request.user,

                query=pending_question,

                location=location_name

            )


            request.session.pop(
                "pending_weather_question",
                None
            )

            request.session.pop(
                "pending_weather_intent",
                None
            )


            return JsonResponse({

                "success": True,

                "reply": reply,

                "location":
                    location_name,

                "ask_location": False

            })


        # If the entered location is invalid,
        # keep waiting for a valid location.

        return JsonResponse({

            "success": False,

            "reply": (
                f"I couldn't find a location named "
                f"<b>{escape_for_html(location)}</b>. "
                f"Please enter a valid city, town, "
                f"district, village or state."
            ),

            "ask_location": True,

            "location": ""

        })


    # -----------------------------------------------------
    # NORMAL CONVERSATION
    # -----------------------------------------------------

    normal_reply = conversational_response(
        message
    )


    if normal_reply:

        save_chat(
            request.user,
            message,
            normal_reply,
            ""
        )


        return JsonResponse({

            "success": True,

            "reply": normal_reply,

            "location": "",

            "ask_location": False

        })


    # -----------------------------------------------------
    # WEATHER QUESTION?
    # -----------------------------------------------------

    if not is_weather_question(message):

        reply = (
            "I can help with weather-related questions. "
            "Try asking about the weather, temperature, "
            "rain, wind, forecast, alerts, safety or climate "
            "for a location."
        )


        save_chat(
            request.user,
            message,
            reply,
            ""
        )


        return JsonResponse({

            "success": True,

            "reply": reply,

            "location": "",

            "ask_location": False

        })


    # -----------------------------------------------------
    # DETECT INTENT
    # -----------------------------------------------------

    intent = detect_intent(
        message
    )


    # -----------------------------------------------------
    # DETECT LOCATION
    # -----------------------------------------------------

    location = detect_location(
        message
    )


    # -----------------------------------------------------
    # LOCATION NOT PROVIDED
    # -----------------------------------------------------

    if not location:

        request.session[
            "pending_weather_question"
        ] = message


        request.session[
            "pending_weather_intent"
        ] = intent


        reply = (
            "Sure 🌦️ Which city, town, district, "
            "village or state should I check?"
        )


        save_chat(
            request.user,
            message,
            reply,
            ""
        )


        return JsonResponse({

            "success": True,

            "reply": reply,

            "location": "",

            "ask_location": True

        })


    # -----------------------------------------------------
    # FETCH WEATHER
    # -----------------------------------------------------

    weather = get_weather(
        location
    )


    if weather is None:

        reply = (
            f"I couldn't find reliable weather information "
            f"for <b>{escape_for_html(location)}</b>."
            "<br><br>"
            "Please check the place name and try again."
        )


        save_chat(
            request.user,
            message,
            reply,
            ""
        )


        return JsonResponse({

            "success": False,

            "reply": reply,

            "location": "",

            "ask_location": False

        })


    # -----------------------------------------------------
    # CREATE WEATHER ANSWER
    # -----------------------------------------------------

    reply = weather_reply(
        weather,
        intent
    )


    location_name = build_location_name(
        weather
    )


    # -----------------------------------------------------
    # SAVE CHAT
    # -----------------------------------------------------

    save_chat(
        request.user,
        message,
        reply,
        location_name
    )


    # -----------------------------------------------------
    # SAVE RECENT SEARCH
    # -----------------------------------------------------

    RecentSearch.objects.create(

        user=request.user,

        query=message,

        location=location_name

    )


    # -----------------------------------------------------
    # KEEP ONLY LATEST 10 SEARCHES
    # -----------------------------------------------------

    searches = (
        RecentSearch.objects
        .filter(
            user=request.user
        )
        .order_by(
            "-created_at"
        )
    )


    old_searches = searches[10:]


    for search in old_searches:

        search.delete()


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return JsonResponse({

        "success": True,

        "reply": reply,

        "location":
            location_name,

        "ask_location": False

    })


# =========================================================
# SAFE HTML TEXT
# =========================================================

def escape_for_html(text):

    replacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
    }


    return "".join(
        replacements.get(
            character,
            character
        )
        for character in str(text)
    )
# =========================================================
# DELETE ONE RECENT SEARCH
# =========================================================

@login_required(login_url="login")
@require_POST
def delete_search(request, search_id):

    search = (
        RecentSearch.objects
        .filter(
            id=search_id,
            user=request.user
        )
        .first()
    )


    if search:

        search.delete()

        return JsonResponse({

            "success": True,

            "message":
                "Recent search deleted."

        })


    return JsonResponse({

        "success": False,

        "message":
            "Recent search not found."

    })


# =========================================================
# CLEAR ALL RECENT SEARCHES
# =========================================================

@login_required(login_url="login")
@require_POST
def clear_searches(request):

    RecentSearch.objects.filter(
        user=request.user
    ).delete()


    return JsonResponse({

        "success": True,

        "message":
            "Recent searches cleared."

    })


# =========================================================
# CLEAR CHAT HISTORY
# =========================================================

@login_required(login_url="login")
@require_POST
def clear_chats(request):

    ChatHistory.objects.filter(
        user=request.user
    ).delete()


    request.session.pop(
        "pending_weather_question",
        None
    )

    request.session.pop(
        "pending_weather_intent",
        None
    )


    return JsonResponse({

        "success": True,

        "message":
            "Chat history cleared."

    })