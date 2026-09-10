from django.urls import path
from .views import smart_campus_page, smart_campus_api

urlpatterns = [
    path("", smart_campus_page, name="smart_campus"),
    path("api/", smart_campus_api, name="smart_campus_api"),
]