from django.db import models
from django.contrib.auth.signals import user_logged_in
import datetime


class LoginAttempt(models.Model):
    username = models.CharField(max_length=255, null=True, blank=True)
    count = models.PositiveIntegerField(null=True, blank=True, default=0)
    timestamp = models.DateTimeField(auto_now_add=True)


class LoginAttemptLogger(object):

    def reset(self, username):
        defaults = {
            'count': 0,
            'timestamp': datetime.datetime.now()
        }
        LoginAttempt.objects.update_or_create(username=username, defaults=defaults)

    def increment(self, username):
        obj, created = LoginAttempt.objects.get_or_create(username=username)
        obj.count += 1
        obj.timestamp = datetime.datetime.now()
        obj.save()


class Log(models.Model):
    class Meta:
        abstract = True
        ordering = ['-timestamp']

    username = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.CharField(max_length=40, null=True, blank=True, verbose_name = "IP")
    forwarded_by = models.CharField(max_length=1000, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class FailedLoginLog(Log):
    pass

class LoginLog(Log):
    pass

class LoginLogger(object):

    def log_failed_login(self, username, request):
        fields = self.extract_log_info(username, request)
        log = FailedLoginLog.objects.create(**fields)

    def log_login(self, username, request):
        fields = self.extract_log_info(username, request)
        log = LoginLog.objects.create(**fields)

    def extract_log_info(self, username, request):
        if request:
            ip_address, proxies = self.extract_ip_address(request)
            user_agent = request.META.get('HTTP_USER_AGENT')
        else:
            ip_address = None
            proxies = None
            user_agent = None

        return {
            'username': username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'forwarded_by': ",".join(proxies or [])
        }

    def extract_ip_address(self, request):
        client_ip = request.META.get('REMOTE_ADDR')
        proxies = None
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for is not None:
            closest_proxy = client_ip
            forwarded_for_ips = [ip.strip() for ip in forwarded_for.split(',')]
            client_ip = forwarded_for_ips.pop(0)
            forwarded_for_ips.reverse()
            proxies = [closest_proxy] + forwarded_for_ips

        return (client_ip, proxies)


login_logger = LoginLogger()
login_attempt_logger = LoginAttemptLogger()
def login_callback(sender, user, request, **kwargs):
    login_logger.log_login(user.get_username(), request)
    login_attempt_logger.reset(user.get_username())

# User logged in Django signal
user_logged_in.connect(login_callback)


# Import password expiry module so that the signal is registered.
# The password expiry feature won't be active unless the necessary
# settings are present.
from . import password_expiry  # noqa
