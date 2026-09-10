from django.urls import path
from .views import travel_assistant_page, travel_assistant_api

urlpatterns = [
    path("", travel_assistant_page, name="travel_assistant"),
    path("api/", travel_assistant_api, name="travel_assistant_api"),
]