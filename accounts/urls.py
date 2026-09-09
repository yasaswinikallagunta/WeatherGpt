from django.urls import path
from .views import signup_view, login_view, home_view, logout_view, profile_view

urlpatterns = [
    path("", signup_view, name="signup"),
    path("login/", login_view, name="login"),
    path("home/", home_view, name="home"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile"),
]