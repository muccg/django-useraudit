import threading
try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    class MiddlewareMixin(object):
        def __init__(self, *args, **kwargs):
            pass

thread_data = threading.local()


def get_request():
    return getattr(thread_data, 'request', None)


class RequestToThreadLocalMiddleware(MiddlewareMixin):

    def process_request(self, request):
        thread_data.request = request
