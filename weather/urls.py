from django.urls import path
from .views import weather_page, weather_api, openweather_test, weatherapi_test

urlpatterns = [
    path("", weather_page, name="weather"),
    path("api/", weather_api, name="weather_api"),
    path("openweather-test/", openweather_test, name="openweather_test"),
    path("weatherapi-test/", weatherapi_test, name="weatherapi_test"),
]