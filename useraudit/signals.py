from django.dispatch import Signal

password_will_expire_warning = Signal()
password_has_expired = Signal()
account_has_expired = Signal()
login_failure_limit_reached = Signal()
