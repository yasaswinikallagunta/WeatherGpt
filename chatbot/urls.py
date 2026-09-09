from django.urls import path

from .views import (
    chatbot_page,
    chatbot_api,
    delete_search,
    clear_searches,
    clear_chats,
)


urlpatterns = [

    path(
        "",
        chatbot_page,
        name="chatbot"
    ),

    path(
        "api/",
        chatbot_api,
        name="chatbot_api"
    ),

    path(
        "delete-search/<int:search_id>/",
        delete_search,
        name="delete_search"
    ),

    path(
        "clear-searches/",
        clear_searches,
        name="clear_searches"
    ),

    path(
        "clear-chats/",
        clear_chats,
        name="clear_chats"
    ),

]