import logging
import abc
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import PermissionDenied
from .models import LoginLogger, LoginAttempt
from .models import LoginAttemptLogger
from .middleware import get_request

logger = logging.getLogger("django.security")


class AuthFailedLoggerBackend(object):

    supports_inactive_user = False

    def __init__(self):
        self.login_logger = LoginLogger()
        self.login_limit = getattr(settings, 'LOGIN_FAILURE_LIMIT', None)
        self.login_attempt_logger = LoginAttemptLogger()

    def authenticate(self, **credentials):
        UserModel = get_user_model()
        self.username = credentials.get(get_user_model().USERNAME_FIELD)
        self.login_logger.log_failed_login(self.username, get_request())
        self.login_attempt_logger.increment(self.username)
        self.attemps_status()

        return None

    def attemps_status(self):
        if self.is_login_limit():
            logger.info("Login failure limit is enabled")
            if self.is_attempts_exceeded() and self._deactivate_user():
                self.notification()
                raise PermissionDenied("Username '%s' has been blocked" % self.username)


    def is_login_limit(self):
        if self.login_limit and self.login_limit > 0:
            return True
        return False
    
    def is_attempts_exceeded(self,):
        count = self._get_count()
        if count and count >= self.login_limit:
            return True
        return False
    
    def _get_count(self):
        try:
            obj = LoginAttempt.objects.get(username = self.username)
            return obj.count
        except LoginAttempt.DoesNotExist:
            return None

    def _get_user(self):
        UserModel = get_user_model()
        try:
            return UserModel._default_manager.get_by_natural_key(self.username)
        except UserModel.DoesNotExist:
            logger.warning("User model for username %s not found" % self.username)
            return None

    def _deactivate_user(self):
        user = self._get_user()
        if user:
            user.is_active = False
            user.save(update_fields=["is_active"])
            logger.warning("Username '%s' has been blocked" % self.username)
            return True
        return False
  
    @abc.abstractmethod
    def notification(self):
        """Place for notification to user that the account has been blocked (Email, SMS etc.)"""
        return
