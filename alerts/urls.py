from django.urls import path
from .views import alerts_page, alerts_api

urlpatterns = [
    path("", alerts_page, name="alerts"),
    path("api/", alerts_api, name="alerts_api"),
]