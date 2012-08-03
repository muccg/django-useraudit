from django.db import models

class FailedLogin(models.Model):
    username = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.CharField(max_length=40, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
