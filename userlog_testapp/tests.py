from datetime import timedelta
from django.contrib.auth import authenticate
from django.core import mail
from django.core import management
from django.dispatch import receiver
from django.test import TestCase, override_settings
from django.utils import timezone
import re

from userlog_testapp.models import MyUser
import userlog.password_expiry


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


    ###########################################################################
    # password expiry test cases

    @override_settings(PASSWORD_EXPIRY_DAYS=5)
    def test_password_not_expired(self):
        u = self.authenticate()
        self.assertIsNotNone(u)
        self.assertTrue(u.is_active)

    @override_settings(PASSWORD_EXPIRY_DAYS=5)
    def test_password_expired(self):
        self.setuser(password_change_date=timezone.now() - timedelta(days=6))
        u = self.authenticate()
        self.assertIsNone(u)
        self.assertTrue(self.user2.is_active)

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


@receiver(userlog.password_expiry.password_has_expired)
def handle_password_expired(**kwargs):
    ExpiryTestCase.password_expired_signal = kwargs


@receiver(userlog.password_expiry.account_has_expired)
def handle_account_expired(**kwargs):
    ExpiryTestCase.account_expired_signal = kwargs
