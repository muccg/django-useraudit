from django.http import HttpResponse, HttpResponseNotFound
from . import middleware


def test_request_available(request):
    thread_request = middleware.get_request()
    if thread_request == request:
        return HttpResponse('OK')
    return HttpResponseNotFound()
