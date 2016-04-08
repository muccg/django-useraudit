import logging
import abc

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from .models import LoginLogger, LoginAttempt
from .middleware import get_request
from django.conf import settings

logger = logging.getLogger("django.security")


class LoginAttemptsBackend(object):

    def __init__(self):
        self.login_logger = LoginLogger()
        self.login_limit = getattr(settings, 'LOGIN_FAILURE_LIMIT', None)

    def authenticate(self, **credentials):
        if self.is_login_limit():
            logger.info("Login failure limit is enabled")
            username = credentials['username']
            count = self._get_count(username)
            if count and count >= self.login_limit:
                if self._deactivate_user(username):
                    logger.warning("Username '%s' has been blocked" % username)
                    self.notification()
                    raise PermissionDenied("Username '%s' has been blocked" % username)
        return None

    def is_login_limit(self):
        if self.login_limit and self.login_limit > 0:
            return True
        return False
    
    def _get_count(self, username):
        try:
            obj = LoginAttempt.objects.get(username = username)
            return obj.count
        except LoginAttempt.DoesNotExist:
            return None

    def _get_user(self, username):
        UserModel = get_user_model()
        try:
            return UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            logger.warning("User model for username %s not found" % username)
            return None

    def _deactivate_user(self, username):
        user = self._get_user(username)
        if user:
            user.is_active = False
            user.save(update_fields=["is_active"])
            return True
        return False
  
    @abc.abstractmethod
    def notification(self):
        """Place for notification to user that the account has been blocked (Email, SMS etc.)"""
        return
