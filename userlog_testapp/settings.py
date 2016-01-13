DEBUG = True
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "userlog",
    "userlog_testapp"
]
AUTH_USER_MODEL = "userlog_testapp.MyUser"
AUTH_USER_MODEL_PASSWORD_CHANGE_DATE_ATTR = "password_change_date"
# PASSWORD_EXPIRY_DAYS = 10
# PASSWORD_EXPIRY_WARNING_DAYS = 7
# ACCOUNT_EXPIRY_DAYS = 5
AUTHENTICATION_BACKENDS = (
    'userlog.password_expiry.UserExpiryBackend',
    'django.contrib.auth.backends.ModelBackend',
    'userlog.backend.AuthFailedLoggerBackend',
)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
SECRET_KEY = "."
TEMPLATES = []
