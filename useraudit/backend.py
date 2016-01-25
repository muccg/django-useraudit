from django.contrib.auth import get_user_model
from .models import LoginLogger
from .middleware import get_request

class AuthFailedLoggerBackend(object):

    supports_inactive_user = False

    def __init__(self):
        self.login_logger = LoginLogger()

    def authenticate(self, **credentials):
        UserModel = get_user_model()
        username = credentials.get(UserModel.USERNAME_FIELD, None)
        username = username or credentials.get('username')
        self.login_logger.log_failed_login(username, get_request())

        return None
