from django.urls import path
from .views import forecast_page, forecast_api

urlpatterns = [
    path("", forecast_page, name="forecast"),
    path("api/", forecast_api, name="forecast_api"),
]