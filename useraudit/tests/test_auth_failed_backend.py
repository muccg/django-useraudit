from django.test import TestCase

from ..backend import AuthFailedLoggerBackend
from .. import models as m
from .utils import chain_maps, is_recent, simulate_login


class AuthFailedBackendTest(TestCase):

    def setUp(self):
        self.be = AuthFailedLoggerBackend()

    def test_log_is_empty(self):
        self.assertEquals(m.FailedLoginLog.objects.count(), 0)

    def test_authenticate_is_logged(self):
        self.be.authenticate()
        self.assertEquals(m.FailedLoginLog.objects.count(), 1)

    def test_authenticate_request_logs_username(self):
        self.be.authenticate(username='some_user')
        log = m.FailedLoginLog.objects.all()[0]
        self.assertEquals(log.username, 'some_user')
        self.assertTrue(is_recent(log.timestamp), 'Should have logged it recently')


class AuthFailedBackendEndToEndTest(TestCase):
    WRONG_CREDENTIALS = {'username': 'some_user', 'password': 'some_pass'}
    DEFAULT_HEADERS = {'REMOTE_ADDR': '192.168.1.2', 'HTTP_USER_AGENT': 'Some user agent'}

    def login(self, **headers):
        all_headers = self.DEFAULT_HEADERS if not headers else chain_maps(headers, self.DEFAULT_HEADERS)
        simulate_login(headers=all_headers, **self.WRONG_CREDENTIALS)

    def test_authenticate_request_logs(self):
        self.login()

        self.assertEquals(m.FailedLoginLog.objects.count(), 1)
        log = m.FailedLoginLog.objects.all()[0]
        self.assertEquals(log.username, 'some_user')
        self.assertTrue(is_recent(log.timestamp), 'Should have logged it recently')
        self.assertEquals(log.ip_address, '192.168.1.2')
        self.assertEquals(log.user_agent, 'Some user agent')

    def test_login_logs(self):
        self.login()
        self.assertEquals(m.FailedLoginLog.objects.count(), 1)
        log = m.FailedLoginLog.objects.all()[0]
        self.assertEquals(log.username, 'some_user')
        self.assertTrue(is_recent(log.timestamp), 'Should have logged it recently')

    def test_long_user_agent_is_truncated(self):
        user_agent_field_length = m.FailedLoginLog._meta.get_field('user_agent').max_length
        long_user_agent = ('x' * user_agent_field_length) + 'this should be truncated'

        self.login(HTTP_USER_AGENT=long_user_agent)

        log = m.FailedLoginLog.objects.all()[0]
        self.assertEquals(len(log.user_agent), user_agent_field_length)
        self.assertTrue(long_user_agent.startswith(log.user_agent))

    def test_authenticate_request_logs_proxies(self):
        self.login(REMOTE_ADDR='192.168.1.100',
                   HTTP_X_FORWARDED_FOR='192.168.1.2, 10.10.10.10, 20.20.20.20')

        self.assertEquals(m.FailedLoginLog.objects.count(), 1)
        log = m.FailedLoginLog.objects.all()[0]
        self.assertEquals(log.ip_address, '192.168.1.2')
        self.assertEquals(log.forwarded_by, '192.168.1.100,20.20.20.20,10.10.10.10')
