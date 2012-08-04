from django.db import models
from django.contrib.auth.signals import user_logged_in

class Log(models.Model):
    class Meta:
        abstract = True
        ordering = ['-timestamp']

    username = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.CharField(max_length=40, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class FailedLoginLog(Log):
    pass

class LoginLog(Log):
    pass

class LoginLogger(object):

    def log_failed_login(self, username, request):
        fields = self.extract_log_info(username, request)
        log = FailedLoginLog.objects.create(**fields)

    def log_login(self, username, request):
        fields = self.extract_log_info(username, request)
        log = LoginLog.objects.create(**fields)

    def extract_log_info(self, username, request):
        ip_address = None
        user_agent = None
        if request:
            ip_address = self.extract_ip_address(request)
            user_agent = request.META.get('USER_AGENT')
        return {
            'username': username,
            'ip_address': ip_address,
            'user_agent': user_agent
        }

    def extract_ip_address(self, request):
        ip = request.META.get('REMOTE_ADDR')
        forwarded_for = request.META.get('X_FORWARDED_FOR')
        if forwarded_for is not None:
            ip = forwarded_for.split(',')[0].strip()
        return ip

  

login_logger = LoginLogger()
def login_callback(sender, user, request, **kwargs):
    login_logger.log_login(user.username, request)
    
# User logged in Django signal
user_logged_in.connect(login_callback)


