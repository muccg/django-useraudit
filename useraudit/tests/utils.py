from datetime import timedelta
from functools import reduce
from importlib import import_module

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.utils import timezone

from django.test.client import RequestFactory

from .. import middleware


def is_recent(time):
    return timezone.now() - timedelta(seconds=3) < time


def simulate_login(username, password, headers=None):
    rf = RequestFactory()
    request = rf.request(**headers)
    engine = import_module(settings.SESSION_ENGINE)
    request.session = engine.SessionStore()

    # TODO remove when we don't support Django 1.10 anymore
    # request passed in to authenticate only after Django 1.10
    # Also the middleware saving the request to thread local can be dropped
    try:
        user = authenticate(request, username=username, password=password)
    except TypeError:
        middleware.thread_data.request = request
        user = authenticate(username=username, password=password)
    if user:
        login(request, user)


def chain_maps(*args):
    """Similar to collections.ChainMap but returned map is a separate copy (ie. changes
    to original dicts don't change the dict returned from this function)."""
    def merge(d1, d2):
        d1.update(d2)
        return d1

    return reduce(merge, reversed(args), {})
