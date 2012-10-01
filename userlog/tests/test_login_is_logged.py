from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User

from userlog import models as m
from userlog.tests.utils import is_recent

from datetime import datetime, timedelta

class LoginIsLoggedTest(TestCase):

    def setUp(self):
        user = User.objects.create_user(username='john', password='sue')
        user.is_staff = True
        user.save()
  
    def test_login_is_logged(self):
        client = Client(REMOTE_ADDR='192.168.1.1', HTTP_USER_AGENT='Test client')
        client.post('/admin/', {
                    'username': 'john', 
                    'password': 'sue',
                    'this_is_the_login_form': 1,
        })
        self.assertEquals(m.FailedLoginLog.objects.count(), 0)
        self.assertEquals(m.LoginLog.objects.count(), 1)
        log = m.LoginLog.objects.all()[0]
        self.assertEquals(log.username, 'john')
        self.assertTrue(is_recent(log.timestamp), 'Should have logged it recently')
        self.assertEquals(log.ip_address, '192.168.1.1')
        self.assertEquals(log.user_agent, 'Test client')

    def test_ip_forwarded_by_proxies(self):
        client = Client(REMOTE_ADDR='3.3.3.3',
                        HTTP_X_FORWARDED_FOR='192.168.1.1, 1.1.1.1, 2.2.2.2')
        client.post('/admin/', {
                    'username': 'john', 
                    'password': 'sue',
                    'this_is_the_login_form': 1,
        })
        log = m.LoginLog.objects.all()[0]
        self.assertEquals(log.ip_address, '192.168.1.1')
        self.assertEquals(log.forwarded_by, '3.3.3.3,2.2.2.2,1.1.1.1')
 
