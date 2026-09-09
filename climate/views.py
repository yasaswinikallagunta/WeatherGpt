import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET


def climate_page(request):
    return render(
        request,
        "climate/climate.html"
    )


def get_json(url):

    request = Request(
        url,
        headers={
            "User-Agent": "WeatherGPT/1.0",
            "Accept": "application/json"
        }
    )

    with urlopen(request, timeout=25) as response:

        return json.loads(
            response.read().decode("utf-8")
        )


@require_GET
def climate_api(request):

    location = request.GET.get(
        "location",
        ""
    ).strip()

    if not location:

        return JsonResponse({
            "success": False,
            "message": "Please enter a city or location."
        }, status=400)

    try:

        # -----------------------------
        # LOCATION SEARCH
        # -----------------------------

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

        # -----------------------------
        # HISTORICAL CLIMATE DATA
        # Last 30 days
        # -----------------------------

        historical_params = urlencode({

            "latitude": latitude,

            "longitude": longitude,

            "start_date":
                get_date_days_ago(30),

            "end_date":
                get_date_days_ago(1),

            "daily": (
                "temperature_2m_mean,"
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_sum"
            ),

            "timezone": "auto"

        })

        historical_url = (
            "https://archive-api.open-meteo.com/v1/archive?"
            + historical_params
        )

        historical_data = get_json(
            historical_url
        )

        daily = historical_data.get(
            "daily",
            {}
        )

        dates = daily.get(
            "time",
            []
        )

        mean_temperature = daily.get(
            "temperature_2m_mean",
            []
        )

        max_temperature = daily.get(
            "temperature_2m_max",
            []
        )

        min_temperature = daily.get(
            "temperature_2m_min",
            []
        )

        rainfall = daily.get(
            "precipitation_sum",
            []
        )

        # -----------------------------
        # CALCULATE SUMMARY
        # -----------------------------

        valid_mean = [
            value
            for value in mean_temperature
            if value is not None
        ]

        valid_max = [
            value
            for value in max_temperature
            if value is not None
        ]

        valid_min = [
            value
            for value in min_temperature
            if value is not None
        ]

        valid_rain = [
            value
            for value in rainfall
            if value is not None
        ]

        average_temperature = (
            sum(valid_mean) / len(valid_mean)
            if valid_mean
            else None
        )

        highest_temperature = (
            max(valid_max)
            if valid_max
            else None
        )

        lowest_temperature = (
            min(valid_min)
            if valid_min
            else None
        )

        total_rainfall = (
            sum(valid_rain)
            if valid_rain
            else 0
        )

        # -----------------------------
        # CLIMATE INSIGHT
        # -----------------------------

        if average_temperature is not None:

            if average_temperature >= 32:

                temperature_insight = (
                    "The recent period shows "
                    "relatively warm conditions."
                )

            elif average_temperature <= 18:

                temperature_insight = (
                    "The recent period shows "
                    "relatively cool conditions."
                )

            else:

                temperature_insight = (
                    "The recent period shows "
                    "moderate temperature conditions."
                )

        else:

            temperature_insight = (
                "Temperature trend information "
                "is currently unavailable."
            )

        if total_rainfall >= 100:

            rainfall_insight = (
                "Significant rainfall was recorded "
                "during the selected period."
            )

        elif total_rainfall >= 30:

            rainfall_insight = (
                "Moderate rainfall was recorded "
                "during the selected period."
            )

        else:

            rainfall_insight = (
                "Relatively low rainfall was recorded "
                "during the selected period."
            )

        return JsonResponse({

            "success": True,

            "location": {
                "city": city,
                "country": country,
                "latitude": latitude,
                "longitude": longitude
            },

            "summary": {

                "average_temperature":
                    round_value(
                        average_temperature
                    ),

                "highest_temperature":
                    round_value(
                        highest_temperature
                    ),

                "lowest_temperature":
                    round_value(
                        lowest_temperature
                    ),

                "total_rainfall":
                    round_value(
                        total_rainfall
                    )
            },

            "trend": {

                "dates": dates,

                "temperature":
                    mean_temperature,

                "rainfall":
                    rainfall
            },

            "insights": {

                "temperature":
                    temperature_insight,

                "rainfall":
                    rainfall_insight
            }

        })

    except HTTPError as error:

        return JsonResponse({

            "success": False,

            "message":
                "Climate data service returned an error.",

            "error":
                f"HTTP {error.code}"

        }, status=502)

    except URLError as error:

        return JsonResponse({

            "success": False,

            "message":
                "Unable to connect to climate data service.",

            "error":
                str(error.reason)

        }, status=502)

    except Exception as error:

        return JsonResponse({

            "success": False,

            "message":
                "Unable to fetch climate data.",

            "error":
                str(error)

        }, status=500)


def get_date_days_ago(days):

    from datetime import date, timedelta

    return (
        date.today()
        - timedelta(days=days)
    ).isoformat()


def round_value(value):

    if value is None:
        return None

    return round(
        value,
        1
    )