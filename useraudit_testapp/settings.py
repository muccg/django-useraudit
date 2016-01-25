import os
DEBUG = True
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "useraudit",
    "useraudit_testapp"
]
# AUTH_USER_MODEL = "useraudit.MyUser"
AUTH_USER_MODEL_PASSWORD_CHANGE_DATE_ATTR = "password_change_date"
PASSWORD_EXPIRY_DAYS = 10
# PASSWORD_EXPIRY_WARNING_DAYS = 7
ACCOUNT_EXPIRY_DAYS = 5
AUTHENTICATION_BACKENDS = (
    'useraudit.password_expiry.AccountExpiryBackend',
    'django.contrib.auth.backends.ModelBackend',
    'useraudit.backend.AuthFailedLoggerBackend',
)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
#        'NAME': 'db.sqlite3',
    }
}
SECRET_KEY = "."
TEMPLATES = []
MIDDLEWARE_CLASSES = []
SITE_ID = 1
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'CRITICAL'),
        },
    },
}
