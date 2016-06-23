import logging
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.dispatch import receiver, Signal
from django.db.models.signals import pre_save
from .signals import login_failure_limit_reached
from .models import LoginLogger, LoginAttempt
from .models import LoginAttemptLogger
from .middleware import get_request

logger = logging.getLogger("django.security")

@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def user_pre_save(sender, instance=None, raw=False, **kwargs):
    user = instance
    is_new_user = user.pk is None
    if is_new_user or raw:
        return

    # User has been re-activated. Ensure the failed login counter is set to 0 so
    # that the user isn't inactivated on next login by the AuthFailedLoggerBackend
    current_user = sender.objects.get(pk=user.pk)
    if not current_user.is_active and user.is_active:
        LoginAttemptLogger().reset(user.username)


class AuthFailedLoggerBackend(object):

    def __init__(self):
        self.login_logger = LoginLogger()
        self.login_failure_limit = getattr(settings, 'LOGIN_FAILURE_LIMIT', None) or 0
        self.login_attempt_logger = LoginAttemptLogger()

    def authenticate(self, **credentials):
        UserModel = get_user_model()
        self.username = credentials.get(get_user_model().USERNAME_FIELD)
        self.login_logger.log_failed_login(self.username, get_request())
        self.login_attempt_logger.increment(self.username)
        self.block_user_if_needed()

        return None

    def block_user_if_needed(self):
        if not self.is_login_failure_limit_enabled():
            return
        logger.debug("Login failure limit is enabled")
        if self.is_attempts_exceeded():
            self._deactivate_user()
            user = self._get_user()
            login_failure_limit_reached.send(sender=user.__class__, user=user)
            logger.info("Login Prevented for user '%s'! Maximum failed logins %d reached!",
                    self.username, self.login_failure_limit)
            raise PermissionDenied("Username '%s' has been blocked" % self.username)

    def is_login_failure_limit_enabled(self):
        return self.login_failure_limit > 0

    def is_attempts_exceeded(self,):
        count = self._get_count()
        if count and count >= self.login_failure_limit:
            return True
        return False

    def _get_count(self):
        try:
            obj = LoginAttempt.objects.get(username=self.username)
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
