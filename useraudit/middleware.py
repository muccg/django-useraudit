import threading

thread_data = threading.local()

def get_request():
    return getattr(thread_data, 'request', None)

class RequestToThreadLocalMiddleware(object):

    def process_request(self, request):
        thread_data.request = request
