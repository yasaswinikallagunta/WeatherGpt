from django.urls import path
from .views import climate_page, climate_api

urlpatterns = [
    path("", climate_page, name="climate"),
    path("api/", climate_api, name="climate_api"),
]