from django.urls import path
from .views import weather_page, weather_api


urlpatterns = [
    path("", weather_page, name="weather"),
    path("api/", weather_api, name="weather_api"),
]