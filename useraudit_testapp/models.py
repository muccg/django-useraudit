from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
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


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        MyProfile.objects.create(user=instance)
