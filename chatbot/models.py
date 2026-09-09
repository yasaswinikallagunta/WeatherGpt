from django.db import models
from django.contrib.auth.models import User


# =========================================================
# CHAT HISTORY
# =========================================================

class ChatHistory(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    message = models.TextField()

    response = models.TextField()

    location = models.CharField(
        max_length=150,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


    def __str__(self):

        return (
            f"{self.user.username} - "
            f"{self.message[:30]}"
        )


# =========================================================
# RECENT SEARCH
# =========================================================

class RecentSearch(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    query = models.CharField(
        max_length=255
    )

    location = models.CharField(
        max_length=150,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


    def __str__(self):

        return (
            f"{self.user.username} - "
            f"{self.query[:30]}"
        )