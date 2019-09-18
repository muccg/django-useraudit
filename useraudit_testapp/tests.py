from datetime import timedelta
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core import mail
from django.core import management
from django.core.handlers.base import BaseHandler
from django.dispatch import receiver
from django.test import TestCase, override_settings
from django.db.models.signals import pre_save
from django.test.signals import setting_changed
from django.test import Client
from django.utils import timezone
import re
import unittest

from useraudit_testapp.models import MyUser, MyProfile
import useraudit_testapp.urls
import useraudit.password_expiry
from useraudit.signals import login_failure_limit_reached, password_has_expired, account_has_expired, password_will_expire_warning
from useraudit.models import UserDeactivation, LoginAttempt

# Saving a reference to the USER_MODEL set in the settings.py file
# Our pre_save handler in password_expiry.py gets registered just for this sender
# so when we use override_settings to change AUTH_USER_MODEL there is no handler
# registered for the models we override AUTH_USER_MODEL with.
USER_MODEL = settings.AUTH_USER_MODEL


# Connects/disconnects extra pre_save handlers for tests that override AUTH_USER_MODEL
# Also see doc for USER_MODEL above
@receiver(setting_changed)
def register_pre_save_on_AUTH_USER_MODER_change(sender, setting, value, enter, **kwargs):
    if setting == "AUTH_USER_MODEL" and value != USER_MODEL:
        if enter:
            pre_save.connect(useraudit.password_expiry.user_pre_save, sender=value)
        else:
            pre_save.disconnect(useraudit.password_expiry.user_pre_save, sender=value)


@override_settings(AUTH_USER_MODEL="useraudit_testapp.MyUser")
class ExpiryTestCase(TestCase):
    username = "testuser"
    password = "testuser"

    def setUp(self):
        self.user = MyUser.objects.create(
            username=self.username,
            last_login=timezone.now(),
            password_change_date=timezone.now(),
            email="testuser@localhost",
        )
        self.user.set_password(self.password)
        self.user.save()

        type(self).password_expired_signal = None
        type(self).password_will_expire_warning_signal = None
        type(self).account_expired_signal = None

    def tearDown(self):
        self.user.delete()

    def authenticate(self):
        return authenticate(username=self.username, password=self.password)

    @property
    def user2(self):
        self.user.refresh_from_db()
        return self.user

    def setuser(self, **kwargs):
        for attr, val in kwargs.items():
            setattr(self.user, attr, val)
        self.user.save()

    ###########################################################################
    # account expiry test cases

    @override_settings(ACCOUNT_EXPIRY_DAYS=5)
    def test_not_expired(self):
        u = self.authenticate()
        self.assertIsNotNone(u)
        self.assertTrue(u.is_active)

    @override_settings(ACCOUNT_EXPIRY_DAYS=5)
    def test_expired(self):
        self.setuser(last_login=timezone.now() - timedelta(days=6))
        u = self.authenticate()
        self.assertIsNone(u)
        self.assertFalse(self.user2.is_active)

    @override_settings(ACCOUNT_EXPIRY_DAYS=5)
    def test_user_deactivation_saved_on_expiration(self):
        self.setuser(last_login=timezone.now() - timedelta(days=6))
        u = self.authenticate()
        ud = UserDeactivation.objects.get(username=self.username)
        self.assertIsNone(u)
        self.assertIsNotNone(ud)
        self.assertEquals(ud.reason, UserDeactivation.ACCOUNT_EXPIRED)

    @override_settings(ACCOUNT_EXPIRY_DAYS=5)
    def test_user_deactivation_deleted_on_login_success(self):
        self.setuser(last_login=timezone.now() - timedelta(days=6))
        self.authenticate()
        count_before = UserDeactivation.objects.filter(username=self.username).count()
        self.setuser(is_active=True)
        c = Client()
        c.login(username=self.username, password=self.password)
        count_after = UserDeactivation.objects.filter(username=self.username).count()
        self.assertEquals(count_before, 1)
        self.assertEquals(count_after, 0)

    @override_settings(ACCOUNT_EXPIRY_DAYS=-5)
    def test_expiry_disabled(self):
        self.setuser(last_login=timezone.now() - timedelta(days=10000))
        u = self.authenticate()
        self.assertIsNotNone(u)
        self.assertTrue(u.is_active)

    @override_settings(ACCOUNT_EXPIRY_DAYS=5)
    def test_fresh_user(self):
        self.setuser(last_login=None)
        u = self.authenticate()
        self.assertIsNotNone(u)
        self.assertTrue(u.is_active)

    @override_settings(ACCOUNT_EXPIRY_DAYS=5)
    def test_authentication_works_if_reactivated(self):
        self.setuser(last_login=timezone.now() - timedelta(days=6))
        u = self.authenticate()
        # User is inactive now

        # Reactivate user
        self.user.is_active = True
        self.user.save()
        u = self.authenticate()
        self.assertIsNotNone(u, "Should be able to log in again if it has been activated")
        self.assertTrue(self.user2.is_active)


    ###########################################################################
    # password expiry test cases

    def test_changing_of_password_updates_password_change_date_field(self):
        self.setuser(password_change_date=timezone.now() - timedelta(days=1))
        before_the_change = timezone.now()
        self.user.set_password("the new password")
        self.user.save()
        self.user.refresh_from_db()
        self.assertGreater(self.user.password_change_date, before_the_change)

    # Keeping the test to remind us about this behaviour
    @unittest.skip("currently changing the password to the previous password is considered a password change")
    def test_saving_same_password_does_not_update_password_change_date_field(self):
        one_day_ago = password_change_date=timezone.now() - timedelta(days=1)
        self.setuser(password_change_date=one_day_ago)
        self.user.set_password("testuser") # same password
        self.user.save()
        self.user.refresh_from_db()
        self.assertEquals(one_day_ago, self.user.password_change_date, "Password change date shouldn't change")


    @override_settings(PASSWORD_EXPIRY_DAYS=5)
    def test_password_not_expired(self):
        u = self.authenticate()
        self.assertIsNotNone(u)
        self.assertTrue(u.is_active)

    @override_settings(PASSWORD_EXPIRY_DAYS=1, PASSWORD_EXPIRY_WARNING_DAYS=1)
    def test_no_warning_if_password_already_expired(self):
        self.setuser(password_change_date=timezone.now() - timedelta(days=2))
        u = self.authenticate()
        self.assertIsNone(self.password_will_expire_warning_signal)

    @override_settings(PASSWORD_EXPIRY_DAYS=1, PASSWORD_EXPIRY_WARNING_DAYS=1)
    def test_password_needs_to_be_changed_today(self):
        u = self.authenticate()
        self.assertTrue(self.user2.is_active)
        self.assertIsNotNone(self.password_will_expire_warning_signal)
        self.assertEquals(self.password_will_expire_warning_signal["sender"], type(self.user))
        self.assertEquals(self.password_will_expire_warning_signal["user"], self.user)
        self.assertEquals(self.password_will_expire_warning_signal["days_left"], 0)

    @override_settings(PASSWORD_EXPIRY_DAYS=1, PASSWORD_EXPIRY_WARNING_DAYS=None)
    def test_no_warning_if_disabled(self):
        u = self.authenticate()
        self.assertIsNone(self.password_will_expire_warning_signal)

    @override_settings(PASSWORD_EXPIRY_DAYS=10, PASSWORD_EXPIRY_WARNING_DAYS=5)
    def test_no_warning_if_warning_days_is_not_big_enough(self):
        # Password is good for 6 more days
        self.setuser(password_change_date=timezone.now() - timedelta(days=3))
        u = self.authenticate()
        self.assertIsNone(self.password_will_expire_warning_signal)

    @override_settings(PASSWORD_EXPIRY_DAYS=10, PASSWORD_EXPIRY_WARNING_DAYS=5)
    def test_warning_as_soon_as_warning_days_is_reached(self):
        # Password is good for 5 more days
        self.setuser(password_change_date=timezone.now() - timedelta(days=4))
        u = self.authenticate()
        self.assertTrue(self.user2.is_active)
        self.assertIsNotNone(self.password_will_expire_warning_signal)
        self.assertEquals(self.password_will_expire_warning_signal["sender"], type(self.user))
        self.assertEquals(self.password_will_expire_warning_signal["user"], self.user)
        self.assertEquals(self.password_will_expire_warning_signal["days_left"], 5)


    @override_settings(PASSWORD_EXPIRY_DAYS=5)
    def test_password_expired(self):
        self.setuser(password_change_date=timezone.now() - timedelta(days=6))
        u = self.authenticate()
        self.assertIsNone(u)
        self.assertFalse(self.user2.is_active)

    @override_settings(PASSWORD_EXPIRY_DAYS=5)
    def test_user_deactivation_saved_on_password_expired(self):
        self.setuser(password_change_date=timezone.now() - timedelta(days=6))
        u = self.authenticate()
        ud = UserDeactivation.objects.get(username=self.username)
        self.assertIsNone(u)
        self.assertIsNotNone(ud)
        self.assertFalse(self.user2.is_active)
        self.assertEquals(ud.reason, UserDeactivation.PASSWORD_EXPIRED)

    @override_settings(PASSWORD_EXPIRY_DAYS=-5)
    def test_password_expiry_disabled(self):
        self.setuser(password_change_date=timezone.now() - timedelta(days=10000))
        u = self.authenticate()
        self.assertIsNotNone(u)
        self.assertTrue(u.is_active)

    @override_settings(PASSWORD_EXPIRY_DAYS=5)
    def test_fresh_user_password(self):
        self.setuser(password_change_date=None)
        u = self.authenticate()
        self.assertIsNotNone(u)
        self.assertTrue(u.is_active)

    @override_settings(PASSWORD_EXPIRY_DAYS=5)
    def test_password_expired_signal(self):
        self.setuser(password_change_date=timezone.now() - timedelta(days=6))
        self.authenticate()
        self.assertIsNotNone(self.password_expired_signal)
        self.assertEquals(self.password_expired_signal["sender"], type(self.user))
        self.assertEquals(self.password_expired_signal["user"], self.user)

    ###########################################################################
    # account expiry notification test cases

    @override_settings(ACCOUNT_EXPIRY_DAYS=5)
    def test_command_notification(self):
        self.setuser(last_login=timezone.now() - timedelta(days=6))
        management.call_command("disable_inactive_users", verbosity=0, email=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(re.search(r"expired", mail.outbox[0].subject, re.I))

    ###########################################################################
    # inactive account test cases

    def test_user_is_active(self):
        self.setuser(is_active=False)
        user = self.authenticate()
        self.assertIsNone(user)


@receiver(password_has_expired)
def handle_password_expired(**kwargs):
    ExpiryTestCase.password_expired_signal = kwargs


@receiver(password_will_expire_warning)
def handle_password_will_expire_warning(**kwargs):
    ExpiryTestCase.password_will_expire_warning_signal = kwargs


@receiver(account_has_expired)
def handle_account_expired(**kwargs):
    ExpiryTestCase.account_expired_signal = kwargs


@override_settings(
    AUTH_USER_MODEL="auth.User",
    AUTH_USER_MODEL_PASSWORD_CHANGE_DATE_ATTR="myprofile.password_change_date",
)
class ProfileExpiryTestCase(TestCase):
    username = "testuser"
    password = "testuser"

    def setUp(self):
        self.user = User.objects.create(
            username=self.username,
            last_login=timezone.now(),
            email="testuser@localhost",
        )
        self.user.set_password(self.password)
        self.user.save()

    def tearDown(self):
        self.user.delete()

    def authenticate(self):
        return authenticate(username=self.username, password=self.password)

    @property
    def user2(self):
        self.user.refresh_from_db()
        return self.user

    ###########################################################################
    # user profile password expiry test cases

    def test_changing_of_password_updates_password_change_date_field(self):
        self.user.myprofile.password_change_date = timezone.now() - timedelta(days=1)
        self.user.myprofile.save()
        before_the_change = timezone.now()
        self.user.set_password("the new password")
        self.user.save()
        self.user.refresh_from_db()
        self.assertGreater(self.user.myprofile.password_change_date, before_the_change)

    @override_settings(PASSWORD_EXPIRY_DAYS=5)
    def test_password_not_expired(self):
        u = self.authenticate()
        self.assertIsNotNone(u)
        self.assertTrue(u.is_active)

    @override_settings(PASSWORD_EXPIRY_DAYS=5)
    def test_password_expired(self):
        self.user.myprofile.password_change_date = timezone.now() - timedelta(days=6)
        self.user.myprofile.save()
        u = self.authenticate()
        self.assertIsNone(u)
        self.assertFalse(self.user2.is_active)

    @override_settings(
        AUTH_USER_MODEL_PASSWORD_CHANGE_DATE_ATTR="myprofile.asdfgh",
    )
    def test_password_expired_bad_attr(self):
        u = self.authenticate()
        # fixme: need to check for log warning
        self.assertIsNotNone(u)

    @override_settings(
        PASSWORD_EXPIRY_DAYS=5,
        AUTH_USER_MODEL_PASSWORD_CHANGE_DATE_ATTR="myprofile.user.myprofile.user.myprofile.password_change_date",
    )
    def test_password_expired_attr(self):
        self.user.myprofile.password_change_date = timezone.now() - timedelta(days=6)
        self.user.myprofile.save()
        u = self.authenticate()
        self.assertIsNone(u)
        self.assertFalse(self.user2.is_active)


@override_settings(LOGIN_FAILURE_LIMIT=2)
class FailedLoginAttemtpsTestCase(TestCase):
    username = "testuser"
    password = "testuser"

    def setUp(self):
        self.user = User.objects.create(
            username=self.username,
            email="testuser@localhost",
        )
        self.user.set_password(self.password)
        self.user.save()

    def tearDown(self):
        self.user.delete()

    @property
    def user2(self):
        self.user.refresh_from_db()
        return self.user

    def test_authenticate_works(self):
        u = authenticate(username=self.username, password=self.password)
        self.assertIsNotNone(u)
        self.assertTrue(u.is_active)

    @override_settings(LOGIN_FAILURE_LIMIT=None)
    def test_login_failure_limit_not_enabled_None(self):
        for i in range(10):
            _ = authenticate(username=self.username, password="INCORRECT")
        u = authenticate(username=self.username, password=self.password)
        self.assertIsNotNone(u)
        self.assertTrue(self.user2.is_active)

    @override_settings(LOGIN_FAILURE_LIMIT=0)
    def test_login_failure_limit_not_enabled_zero(self):
        for i in range(10):
            _ = authenticate(username=self.username, password="INCORRECT")
        u = authenticate(username=self.username, password=self.password)
        self.assertIsNotNone(u)
        self.assertTrue(self.user2.is_active)

    def test_login_failure_limit_reached(self):
        _ = authenticate(username=self.username, password="INCORRECT")
        _ = authenticate(username=self.username, password="INCORRECT")
        u = authenticate(username=self.username, password=self.password)
        self.assertIsNone(u)
        self.assertFalse(self.user2.is_active)

    def test_user_deactivation_saved_when_login_failure_limit_reached(self):
        _ = authenticate(username=self.username, password="INCORRECT")
        _ = authenticate(username=self.username, password="INCORRECT")
        u = authenticate(username=self.username, password=self.password)
        ud = UserDeactivation.objects.get(username=self.username)
        self.assertIsNone(u)
        self.assertIsNotNone(ud)
        self.assertEquals(ud.reason, UserDeactivation.TOO_MANY_FAILED_LOGINS)

    def test_user_deactivation_NOT_saved_when_login_failure_limit_reached_but_username_does_NOT_exist(self):
        username = 'doesnotexit'
        _ = authenticate(username=username, password="INCORRECT")
        _ = authenticate(username=username, password="INCORRECT")
        u = authenticate(username=username, password=self.password)
        uds = UserDeactivation.objects.filter(username=username).count()
        self.assertIsNone(u)
        self.assertEquals(uds, 0)

    def test_failure_counter_reset_when_reactivated(self):
        _ = authenticate(username=self.username, password="INCORRECT")
        _ = authenticate(username=self.username, password="INCORRECT")
        _ = authenticate(username=self.username, password="INCORRECT")
        # User is inactive now
        # Reactivate user
        self.user.is_active = True
        self.user.save()

        # IF the counter wasn't reset to 0, the first failed login attempt
        # would inactivate the user again.
        _ = authenticate(username=self.username, password="INCORRECT")
        u = authenticate(username=self.username, password=self.password)
        self.assertIsNotNone(u, "Should be able to log after just 1 failed login attempt")
        self.assertTrue(self.user2.is_active)

    def test_signal(self):
        def handler(sender, user=None, **kwargs):
            self.handler_called = True
            self.assertEquals(sender, type(self.user))
            self.assertEquals(user, self.user)
        login_failure_limit_reached.connect(handler)

        self.handler_called = False

        _ = authenticate(username=self.username, password="INCORRECT")
        _ = authenticate(username=self.username, password="INCORRECT")

        login_failure_limit_reached.disconnect(handler)

        self.assertTrue(self.handler_called)

class LoginAttemtpsTimestampTestCase(TestCase):
    username = "testuser"
    password = "testuser"

    def setUp(self):
        self.user = User.objects.create(
            username=self.username,
            email="testuser@localhost",
        )
        self.user.set_password(self.password)
        self.user.save()

    def tearDown(self):
        self.user.delete()

    @override_settings(USE_TZ=False)
    def test_timestamp_naive(self):
        _ = authenticate(username=self.username, password="INCORRECT")
        _ = authenticate(username=self.username, password="INCORRECT")
        login_attempt = LoginAttempt.objects.get(username=self.username)

        timestamp = login_attempt.timestamp
        is_naive = timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None 
        self.assertTrue(is_naive)

    @override_settings(USE_TZ=True)
    def test_timestamp_aware(self):
        _ = authenticate(username=self.username, password="INCORRECT")
        _ = authenticate(username=self.username, password="INCORRECT")
        login_attempt = LoginAttempt.objects.get(username=self.username)

        timestamp = login_attempt.timestamp
        is_aware = timestamp.tzinfo is not None and timestamp.tzinfo.utcoffset(timestamp) is not None
        self.assertTrue(is_aware)


class MiddlewareTestCase(TestCase):

    @override_settings(MIDDLEWARE_CLASSES=['useraudit.middleware.RequestToThreadLocalMiddleware'])
    def test_middleware_loads_on_PRE_django_1_10s_old_style_middleware(self):
        handler = BaseHandler()
        handler.load_middleware()

    @override_settings(MIDDLEWARE=['useraudit.middleware.RequestToThreadLocalMiddleware'])
    def test_middleware_loads_on_django_1_10s_new_style_middleware(self):
        handler = BaseHandler()
        handler.load_middleware()
