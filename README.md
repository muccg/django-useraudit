# Welcome

[![Build Status](https://travis-ci.org/muccg/django-useraudit.svg)](https://travis-ci.org/muccg/django-useraudit) [![PyPI](https://badge.fury.io/py/django-useraudit.svg)](https://pypi.python.org/pypi/django-useraudit)

Django Useraudit is a small collection of user audit utilities containing:

* log basic information about successful and failed login attempts to the database
* disabling accounts of inactive users
* disabling accounts of users who haven't changed their passwords frequently enough

Django Useraudit is developed at [CCG, Murdoch University, Western Australia.](https://ccg.murdoch.edu.au/ "CCG Website")


## Features

### User login log

There are two log tables one for successful and one for failed logins.

Both logs contain the same information:

* Username - the Django user's name who tried to log in
* IP address - the client IP address of the browser (or other HTTP client)
* Forwarded by - list of proxies between the client and the server
* User Agent - the user agent as received by the client
* Timestamp - timestamp of the login request

The *Forwarded by* field can be important, because if you don't trust all the proxies
in the list, then you can't rely on the IP Address being correct.
The proxies are listed from closest (to the server) to furthermost.

### User and password expiry

The settings `ACCOUNT_EXPIRY_DAYS` and `PASSWORD_EXPIRY_DAYS` are provided for
controling how frequently a user should log in and/or change their password before
their account will be disabled.

By default, the user account is disabled at the time the user tries to log in.

If you would like to disable inactive accounts as they expire you should consider running the `disable_inactive_users` custom django management command from a cron job.

### Login attempts limit

The setting `LOGIN_FAILURE_LIMIT` allows to enable a number of allowed failed login attempts.
If the settings is not set or set to 0, the feature is disabled.

When the login failure limit is reached the user account will be deactivated.
The `useraudit.signals.login_failure_limit_reached` signal is sent when this happens to allow
for custom notification.

## Requirements

Has been developed and tested on Django 1.9, but should work on other
versions too.

## Installation

You can install Django Useraudit from PyPI:

```
$ pip install django-useraudit
```

## Configuration

### Adding the useraudit app

Add `useraudit` to your `settings.INSTALLED_APPS`:

```
INSTALLED_APPS = (
...
    'useraudit',
)
```

You will run `migrate` to create/migrate the useraudit DB tables. Ex:

```
$ ./manage.py migrate useraudit
```

### Model changes for password expiration

For password expiration to work we have to save the last time the users changed their password.
Therefore a datetime field is needed that is associated with the User.
However, Django allows two possible ways for you to extend your User model, Django custom auth
models or a "user profile" model that is associated with a OneToOne field to the auth User model.
Django Useraudit can't possibly know which method (if any) your project is using therefore it can't
create this field and the migration for it automatically.
You will have to create the field and your migration manually as follows.

The field definition in both cases should be a `DateTimeField` with `auto_add_now`, and `null` set to `True`.
The recommended name is `password_change_date`, but that is customisable.
Ex:

```
    ...
    password_change_date = models.DateTimeField(auto_now_add=True, null=True)
    ...
```

#### Using a django custom auth model

Add the field definition to your custom auth user model and make your migrations.
Edit your settings accordingly:

```
    AUTH_USER_MODEL = "yourapp.YourCustomUser"
    AUTH_USER_MODEL_PASSWORD_CHANGE_DATE_ATTR = "password_change_date"
```

#### Using a django user profile

Add the field definition to your user profile model and make your migrations.
Set `AUTH_USER_MODEL_PASSWORD_CHANGE_DATE_ATTR` in your settings. The setting should be the complete "path"
from the user object to the field you just added.

```
    AUTH_USER_MODEL_PASSWORD_CHANGE_DATE_ATTR = "yourprofile.password_change_date"
```

### Changes in settings.py

Add `useraudit.middleware.RequestToThreadLocalMiddleware` to
`settings.MIDDLEWARE_CLASSES`:

```
MIDDLEWARE_CLASSES = (
    'useraudit.middleware.RequestToThreadLocalMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
...
)
```

Add `useraudit.backend.AuthFailedLoggerBackend` to
`settings.AUTHENTICATION_BACKENDS` **as the last element** and
`useraudit.password_expiry.AccountExpiryBackend` **as the first element**:

```
AUTHENTICATION_BACKENDS = (
    'useraudit.password_expiry.AccountExpiryBackend',
    'django.contrib.auth.backends.ModelBackend',
    'useraudit.backend.AuthFailedLoggerBackend'
)
```

Configure the settings relevant to account and password expiry:

```
       # How long a user's password is good for. None or 0 means no expiration.
       PASSWORD_EXPIRY_DAYS = 180
       # How long before expiry will the frontend start bothering the user
       PASSWORD_EXPIRY_WARNING_DAYS = 30
       # # Disable the user's account if they haven't logged in for this time
       # ACCOUNT_EXPIRY_DAYS = 100
       # Set to 0 disables the feature
       LOGIN_FAILURE_LIMIT = 3
```

### Password expiration warnings in frontend code

You should add code to your frontend to warn the user if their password is due to expire.
Otherwise one day they will be unable to login and won't know why.


### Enabling the admin site for useraudit

In order to see the logs you will have to enable Django Admin at least
for the useraudit application.

Head to the admin page of your project and see the logs "Failed login
log" and "Login log" under the Useraudit app.

### Cron job to disable inactive accounts (optional)

User accounts that have not been active for `ACCOUNT_EXPIRY_DAYS` will be deactivated the first time the
user logs in. This means that you could have user accounts that are past their `ACCOUNT_EXPIRY_DAYS`, but still
active, because the user haven't tried to log in after they account expired.
In case this worries you, a cron job should be added that runs periodically to deactive expired user accounts.

The cron job should run the `disable_inactive_users` custom Django command.

### Re-activate users

The `activate_user` custom Django management command can be used to re-activate users that have been locked out from the system.

## Done

Useraudit is set up to log all log in attempts for your project and expire user accounts.

In case you would like to know the technical details please see
[how it works](https://github.com/muccg/django-useraudit/wiki/How-it-works).

For developer specific information please see
[development](https://github.com/muccg/django-useraudit/wiki/Development).

