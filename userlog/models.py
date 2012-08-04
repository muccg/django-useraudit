from django.db import models
from django.contrib.auth.signals import user_logged_in

# TODO
#class Log(models.Model):


class FailedLogin(models.Model):
    username = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.CharField(max_length=40, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class LoginLog(models.Model):
    username = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.CharField(max_length=40, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

def log_login(sender, user, request, **kwargs):
    ip_address = None
    user_agent = None
    if request:
        ip_address = extract_ip_address(request)
        user_agent = request.META.get('USER_AGENT')
    LoginLog.objects.create(
        username = user.username,
        ip_address = ip_address,
        user_agent = user_agent
    )
    
def extract_ip_address(request):
    ip = request.META.get('REMOTE_ADDR')
    forwarded_for = request.META.get('X_FORWARDED_FOR')
    if forwarded_for is not None:
        ip = forwarded_for.split(',')[0].strip()
    return ip

user_logged_in.connect(log_login)

