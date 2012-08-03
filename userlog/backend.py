from userlog import models as m
from userlog.middleware import get_request

def get_request_header(name):
    request = get_request()
    if request and name in request.META:
        return request.META[name]

class AuthFailedLoggerBackend(object):
    

    def authenticate(self, **credentials):
        print get_request().META
        username = credentials.get('username')
        ip_address = get_request_header('REMOTE_ADDR')
        user_agent = get_request_header('USER_AGENT')
        m.FailedLogin.objects.create(
            username=username, 
            ip_address=ip_address,
            user_agent=user_agent
        )

        return None
