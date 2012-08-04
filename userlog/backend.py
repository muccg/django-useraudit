from userlog import models as m
from userlog.middleware import get_request

def get_request_header(name):
    request = get_request()
    if request and name in request.META:
        return request.META[name]

class AuthFailedLoggerBackend(object):

    def authenticate(self, **credentials):
        username = credentials.get('username')
        ip_address = self.extract_ip_address()
        user_agent = get_request_header('USER_AGENT')
        m.FailedLogin.objects.create(
            username=username, 
            ip_address=ip_address,
            user_agent=user_agent
        )

        return None

    def extract_ip_address(self):
        ip = get_request_header('REMOTE_ADDR')
        forwarded_for = get_request_header('X_FORWARDED_FOR')
        if forwarded_for is not None:
            ip = forwarded_for.split(',')[0].strip()
        return ip
