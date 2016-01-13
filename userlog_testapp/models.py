from django.db import models
from django.contrib.auth.models import AbstractUser


class MyUser(AbstractUser):
    password_change_date = models.DateTimeField(
        auto_now_add=True,
        null=True,
    )
