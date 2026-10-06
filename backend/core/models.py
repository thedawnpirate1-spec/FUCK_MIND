from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Erweitertes User-Modell für KanMind.
    """
    email = models.EmailField(unique=True)
    color = models.CharField(max_length=7, default='#FF7A00', help_text="Hex color for user badge")

    def __str__(self):
        return f"{self.username} ({self.email})"
