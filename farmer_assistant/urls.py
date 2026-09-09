from django.urls import path
from .views import farmer_assistant_page, farmer_weather_api

urlpatterns = [
    path("", farmer_assistant_page, name="farmer_assistant"),
    path("api/", farmer_weather_api, name="farmer_weather_api"),
]