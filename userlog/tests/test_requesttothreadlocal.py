from django.test import TestCase

from userlog.middleware import get_request

class RequestToThreadLocalMiddlewareTest(TestCase):
   
    def test_request_is_saved(self):
        response = self.client.get('', X_TEST='middleware test')
        request = get_request()
        self.assertTrue(request is not None)
        self.assertEquals(request.META['X_TEST'], 'middleware test')
