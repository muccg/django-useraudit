"""
Django password and account expiry.

This will prevent users from logging in unless they have changed their
password within a configurable password expiry period.

Expired users can reset their password using the normal registration
forms.

It will disable unused accounts. If users haven't logged in for a
certain time period, their account will be disabled next time a login
is attemped.

Requirement for account expiry: whichever user model is used should
implement AbstractBaseUser (standard Django user model does of
course).


How to use:

1. Add "useraudit" to the list of INSTALLED_APPS.

2. Put expiry backend *first* in the list of auth backends::

       AUTHENTICATION_BACKENDS = (
           'useraudit.password_expiry.AccountExpiryBackend',
           # ... the rest ...
       )

3. Use either Option A or Option B depending on your app.
    - A: Django custom auth model
    - B: "Profile" model related OneToOne with stock django User

   Option A: Use a django custom auth model for your users and add a field for
   password expiry::

       # settings.py
       AUTH_USER_MODEL = "myapp.MyUser"
       AUTH_USER_MODEL_PASSWORD_CHANGE_DATE_ATTR = "password_change_date"

       # models.py
       from django.contrib.auth.models import AbstractUser

       class MyUser(AbstractUser):
           password_change_date = models.DateTimeField(
               auto_now_add=True,
               null=True,
           )

   Option B: Use your existing profile model or create a new one, and
   add a field for password expiry::

       # settings.py
       AUTH_USER_MODEL_PASSWORD_CHANGE_DATE_ATTR = "myprofile.password_change_date"

       # models.py
       from django.db import models
       from django.contrib.auth.models import User

       class MyProfile(models.Model):
           user = models.OneToOneField(User, on_delete=models.CASCADE)
           password_change_date = models.DateTimeField(
               auto_now_add=True,
               null=True,
           )


4. Configure the settings relevant to password expiry::

       # How long a user's password is good for. None or 0 means no expiration.
       PASSWORD_EXPIRY_DAYS = 180
       # How long before expiry will the frontend start bothering the user
       PASSWORD_EXPIRY_WARNING_DAYS = 30
       # # Disable the user's account if they haven't logged in for this time
       # ACCOUNT_EXPIRY_DAYS = 100

5. Add log handlers for "django.security" if they aren't already there.

6. Inspect all non-standard login views and make sure they are
   checking for User.is_active.

7. Add code to your frontend to nag the user if their password is due
   to expire. Otherwise one day they will be unable to login and they
   won't know why.

   todo: add an automatic process for e-mailing users before password expiry

8. In your deployment scripts, include a daily cronjob to run the
   disable_inactive_users management command. This will let users know
   if their account has been disabled. It requires the Sites framework
   to be enabled, and for the user model to have an "email" attribute.
"""

from collections import namedtuple
from functools import reduce
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models.signals import pre_save
from django.dispatch import receiver, Signal
from django.utils import timezone
import logging
from .backend import AuthFailedLoggerBackend
from .signals import password_has_expired, account_has_expired

logger = logging.getLogger("django.security")

__all__ = ["AccountExpiryBackend"]

@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def user_pre_save(sender, instance=None, raw=False, **kwargs):
    user = instance
    attrs = ExpirySettings.get()
    # We're saving the password change date only for existing users
    # Users just created should be taken care of by auto_now_add.
    # This way we can assume that a User profile object already exists
    # for the user. This is essential, because password change detection
    # can happen only in pre_save, in post_save it is too late.
    is_new_user = user.pk is None
    if is_new_user or raw:
        return
    if attrs.date_changed:
        update_date_changed(user, attrs.date_changed)

    # User has been re-activated. Ensure the last_login is set to None so
    # that the user isn't inactivated on next login by the AccountExpiryBackend
    current_user = sender.objects.get(pk=user.pk)
    if not current_user.is_active and user.is_active:
        user.last_login = None


def update_date_changed(user, date_changed_attr):
    def did_password_change(user):
        current_user = get_user_model().objects.get(pk=user.pk)
        return current_user.password != user.password

    def save_profile_password_change_date(user, date):
        parts = date_changed_attr.split('.')
        attr_name = parts[-1]
        profile = reduce(lambda obj, attr: getattr(obj, attr), parts[:-1], user)
        setattr(profile, attr_name, date)
        profile.save()

    def set_password_change_date(user, date):
        setattr(user, date_changed_attr, date)

    if did_password_change(user):
        now = timezone.now()
        if '.' in date_changed_attr:
            save_profile_password_change_date(user, now)
        else:
            set_password_change_date(user, now)


def is_password_expired(user):
    earliest = ExpirySettings.get().earliest_possible_password_change
    if earliest:
        change_date = get_password_change_date(user)
        return change_date and change_date < earliest
    return False


def get_password_change_date(user):
    attr = ExpirySettings.get().date_changed
    if attr:
        val = user
        if isinstance(attr, str):
            for part in attr.split("."):
                if hasattr(val, part):
                    val = getattr(val, part)
                else:
                    logger.warning("User model does not have a %s attribute" % attr)
                    return None
            return val
        else:
            logger.warning("Password change attr in settings is not a string")

    return None


def get_user_last_login(user):
    if hasattr(user, "last_login"):
        return user.last_login
    else:
        logger.warning("User model doesn't have last_login field. ACCOUNT_EXPIRY_DAYS setting will have no effect.")
        return None


def is_account_expired(user):
    earliest = ExpirySettings.get().earliest_possible_login
    if earliest:
        last_login = get_user_last_login(user)
        return last_login and last_login < earliest
    return False


class ExpirySettings(namedtuple("ExpirySettings", ["num_days", "num_warning_days", "date_changed", "password", "account_expiry"])):
    @classmethod
    def get(cls):
        expiry = getattr(settings, "PASSWORD_EXPIRY_DAYS", None) or 0
        warning = getattr(settings, "PASSWORD_EXPIRY_WARNING_DAYS", None) or 0
        date_changed = getattr(settings, "AUTH_USER_MODEL_PASSWORD_CHANGE_DATE_ATTR", None) or None
        password = getattr(settings, "AUTH_USER_MODEL_PASSWORD_ATTR", None) or "password"
        account_expiry = getattr(settings, "ACCOUNT_EXPIRY_DAYS", None) or 0
        return cls(expiry, warning, date_changed, password, account_expiry)

    @property
    def earliest_possible_login(self):
        if self.account_expiry > 0:
            return timezone.now() - timedelta(days=self.account_expiry)
        return None

    @property
    def earliest_possible_password_change(self):
        if self.num_days > 0:
            return timezone.now() - timedelta(days=self.num_days)
        return None


class AccountExpiryBackend(object):
    """
    This backend doesn't authenticate, it just prevents authentication
    of a user whose account password has expired.
    """
    def authenticate(self, username=None, password=None, **kwargs):
        user = self._lookup_user(username, password, **kwargs)

        if user:
            # Prevent authentication of inactive users (if the user
            # model supports it). Django only checks is_active at the
            # login view level.
            if hasattr(user, "is_active") and not user.is_active:
                self._prevent_login(username, "Account is not active")

            if is_password_expired(user):
                password_has_expired.send(sender=user.__class__, user=user)
                self._prevent_login(username, "Password has expired")

            if  is_account_expired(user):
                logger.info("Disabling stale user account: %s" % user)
                user.is_active = False
                user.save()
                account_has_expired.send(sender=user.__class__, user=user)
                self._prevent_login(username, "Account has expired")

        # pass on to next handler
        return None

    def _prevent_login(self, username, msg="User login prevented"):
        def is_failed_login_logger_configured():
            auth_backends = getattr(settings, 'AUTHENTICATION_BACKENDS', [])
            return 'useraudit.backend.AuthFailedLoggerBackend' in auth_backends

        logger.info("Login Prevented for user '%s'! %s", username, msg)
        if is_failed_login_logger_configured():
            AuthFailedLoggerBackend().authenticate(username=username)
        raise PermissionDenied(msg)

    def _lookup_user(self, username=None, password=None, **kwargs):
        # This is the same procedure as in
        # django.contrib.auth.backends.ModelBackend, except without
        # the timing attack mitigation, because it doesn't take long
        # to check for expiry.
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            return UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            return None
