import logging

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import LoginAttemptLogger, UserDeactivation
from . import middleware


logger = logging.getLogger("django.security")

login_attempt_logger = LoginAttemptLogger()


def test_request_available(request):
    thread_request = middleware.get_request()
    if thread_request == request:
        return HttpResponse('OK')
    return HttpResponseNotFound()


def reactivate_user(request, user_id):
    user = _get_user(user_id)
    user.is_active = True
    user.save()
    UserDeactivation.objects.filter(username=user.username).delete()
    login_attempt_logger.reset(user.username)
    return HttpResponseRedirect(reverse("admin:useraudit_loginattempt_changelist"))


def _get_user(user_id):
    UserModel = get_user_model()
    try:
        return UserModel.objects.get(id=user_id)
    except UserModel.DoesNotExist:
        logger.warning("User model for user_id %d not found" % user_id)
        return None
