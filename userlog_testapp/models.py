from django.db import models
from django.contrib.auth.models import AbstractUser, User


class MyUser(AbstractUser):
    password_change_date = models.DateTimeField(
        auto_now_add=True,
        null=True,
    )


class MyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    password_change_date = models.DateTimeField(
        auto_now_add=True,
        null=True,
    )
