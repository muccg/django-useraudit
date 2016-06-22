from django.dispatch import Signal

password_has_expired = Signal(providing_args=["user"])
account_has_expired = Signal(providing_args=["user"])
login_failure_limit_reached = Signal(providing_args=["user"])
