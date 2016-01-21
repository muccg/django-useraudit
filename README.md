# Welcome

[![Build Status](https://travis-ci.org/muccg/django-useraudit.svg)](https://travis-ci.org/muccg/django-useraudit)

Django Userlog is a small Django app that allow you to log basic
information about successful and failed login attempts to a database.

## Features

There are two log tables one for successful and one for failed logins.

Both logs contain the same information:

* Username
* IP address
* Forwarded by
* User Agent
* Timestamp

Forwarded by is a comma-separated list of proxies that forwarded the
request for you. The proxies are listed from closest to furthermost.

This field is important, because if you don't trust all the proxies in
the list, then you can't rely on the IP Address being correct.

## Requirements

Has been developed and tested on Django 1.9, but should work on other
versions too.

Supports South migrations for Django 1.7 and lower to make schema
changes easier.

For development the only other requirement is django-discover-runner
for running the unit tests and sqlite3.

## Installation

You can pip install using a link from the releases page:

https://github.com/muccg/django-userlog/releases

Example for version 2.3.0:

```
$ pip install https://github.com/muccg/django-userlog/archive/2.3.0.zip
```


## Configuration

### Adding the userlog app

Add `userlog` to your `settings.INSTALLED_APPS`:

```
INSTALLED_APPS = (
...
    'userlog',
)
```

You will run `migrate` to create/migrate the userlog DB tables. Ex:

```
$ ./manage.py migrate userlog
```

### Changes in settings.py

Add `userlog.middleware.RequestToThreadLocalMiddleware` to
`settings.MIDDLEWARE_CLASSES`:

```
MIDDLEWARE_CLASSES = (
    'userlog.middleware.RequestToThreadLocalMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
...
)
```

Add `userlog.backend.AuthFailedLoggerBackend` to
`settings.AUTHENTICATION_BACKENDS` **as the last element**:

```
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'userlog.backend.AuthFailedLoggerBackend'
)
```

### Enabling the admin site for userlog

In order to see the logs you will have to enable Django Admin at least
for the userlog application.

Head to the admin page of your project and see the logs "Failed login
log" and "Login log" under the Userlog app.

## Done

Userlog is set up and will log all log in attempts for your project.

In case you would like to know the technical details please go to the
[how it works](https://github.com/muccg/django-userlog/wiki/How-it-works)
page.

For developer specific information you probably also want to read the
[development](https://github.com/muccg/django-userlog/wiki/Development)
page.

New releases will be announced on the
[releases](https://github.com/muccg/django-userlog/wiki/Releases)
page.
