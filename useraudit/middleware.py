import threading
from django.utils.deprecation import MiddlewareMixin

thread_data = threading.local()

def get_request():
    return getattr(thread_data, 'request', None)

class RequestToThreadLocalMiddleware(MiddlewareMixin):

    def process_request(self, request):
        thread_data.request = request
