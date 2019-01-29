from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """extending Django user class"""

    title = models.CharField(max_length=30, blank=True)
    test_field = models.CharField(max_length=3, blank=True)
