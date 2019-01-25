from django.db import models
from django.contrib.auth.models import AbstractUser


# *****may want to move this up one level, but should work here for all Django apps
class User(AbstractUser):
    """extending Django user class"""

    title = models.CharField(max_length=30, blank=True)
