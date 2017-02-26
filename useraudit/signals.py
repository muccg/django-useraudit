from django.dispatch import Signal

password_will_expire_warning = Signal(providing_args=["user", "days_left"])
password_has_expired = Signal(providing_args=["user"])
account_has_expired = Signal(providing_args=["user"])
login_failure_limit_reached = Signal(providing_args=["user"])
