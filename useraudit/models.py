from __future__ import unicode_literals
import datetime
import logging
from django.db import models
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in
from .signals import password_has_expired, account_has_expired, login_failure_limit_reached


logger = logging.getLogger('django.security')


class LoginAttempt(models.Model):
    username = models.CharField(max_length=255, null=True, blank=True)
    count = models.PositiveIntegerField(null=True, blank=True, default=0)
    timestamp = models.DateTimeField(auto_now_add=True)


class LoginAttemptLogger(object):

    def reset(self, username):
        defaults = {
            'count': 0,
            'timestamp': timezone.now()
        }
        LoginAttempt.objects.update_or_create(username=username, defaults=defaults)

    def increment(self, username):
        obj, created = LoginAttempt.objects.get_or_create(username=username)
        obj.count += 1
        obj.timestamp = timezone.now()
        obj.save()


class Log(models.Model):
    class Meta:
        abstract = True
        ordering = ['-timestamp']

    username = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.CharField(max_length=40, null=True, blank=True, verbose_name="IP")
    forwarded_by = models.CharField(max_length=1000, null=True, blank=True)
    user_agent = models.CharField(max_length=1000, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s|%s|%s|%s|%s' % (self.username, self.ip_address, self.forwarded_by, self.user_agent, self.timestamp)


class UserDeactivation(models.Model):
    ACCOUNT_EXPIRED = 'AE'
    PASSWORD_EXPIRED = 'PE'
    TOO_MANY_FAILED_LOGINS = 'FL'

    DEACTIVATION_REASON_CHOICES = (
        (ACCOUNT_EXPIRED, 'Account expired'),
        (PASSWORD_EXPIRED, 'Password expired'),
        (TOO_MANY_FAILED_LOGINS, 'Too many failed login attempts'),
    )

    username = models.CharField(max_length=255)
    reason = models.CharField(max_length=2, blank=True, null=True, choices=DEACTIVATION_REASON_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)


class FailedLoginLog(Log):
    pass


class LoginLog(Log):
    pass


class LoginLogger(object):

    def log_failed_login(self, username, request):
        fields = self.extract_log_info(username, request)
        FailedLoginLog.objects.create(**fields)

    def log_login(self, username, request):
        fields = self.extract_log_info(username, request)
        LoginLog.objects.create(**fields)

    def extract_log_info(self, username, request):
        USER_AGENT_MAX_LENGTH = Log._meta.get_field('user_agent').max_length
        if request:
            ip_address, proxies = self.extract_ip_address(request)
            user_agent = request.META.get('HTTP_USER_AGENT')
        else:
            ip_address = None
            proxies = None
            user_agent = None

        if user_agent is not None and len(user_agent) > USER_AGENT_MAX_LENGTH:
            logger.warning('Truncating User Agent to fit into %d. Original was: "%s"',
                           USER_AGENT_MAX_LENGTH, user_agent)
            user_agent = user_agent[:USER_AGENT_MAX_LENGTH]

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
    username = user.get_username()
    login_logger.log_login(username, request)
    login_attempt_logger.reset(username)
    UserDeactivation.objects.filter(username=username).delete()


# User logged in Django signal
user_logged_in.connect(login_callback)


def save_login_deactivation(reason):
    def callback(sender, user, **kwargs):
        username = user.get_username()
        UserDeactivation.objects.filter(username=username).delete()
        UserDeactivation.objects.create(username=username, reason=reason)
    return callback


password_expired_callback = save_login_deactivation(UserDeactivation.PASSWORD_EXPIRED)
account_expired_callback = save_login_deactivation(UserDeactivation.ACCOUNT_EXPIRED)
login_failure_limit_reached_callback = save_login_deactivation(UserDeactivation.TOO_MANY_FAILED_LOGINS)


password_has_expired.connect(password_expired_callback)
account_has_expired.connect(account_expired_callback)
login_failure_limit_reached.connect(login_failure_limit_reached_callback)


# Import password expiry module so that the signal is registered.
# The password expiry feature won't be active unless the necessary
# settings are present.
from . import password_expiry  # noqa
