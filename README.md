== Welcome ==

Django Userlog is a small Django app that allow you to log basic information about successful and failed login attempts to a database.

=== Features ===

There are two log tables one for successful and one for failed logins.

Both logs contain the same information:

* Username
* IP address
* Forwarded by
* User Agent
* Timestamp

Forwarded by is a comma-separated list of proxies that forwarded the request for you. The proxies are listed from closest to furthermost.
This field is important, because if you don't trust all the proxies in the list, then you can't rely on the IP Address being correct.

=== Requirements ===

Has been developed and tested on Django 1.4.1, but should work on other versions too.

Uses South to make further upgrades that require schema changes easier.

For development the only other requirement is django-discover-runner for running the unit tests and sqlite3.

=== Installation ===

You can pip install using a link from the downloads page: 

https://bitbucket.org/ahunter_ccg/django-userlog/downloads

Example for version 0.1:

{{{
$ pip install https://bitbucket.org/ahunter_ccg/django-userlog/downloads/django_userlog-0.1.tar.gz
}}}

or download the latest version from the downloads page and easy_install it:

Example for version 0.1:
{{{
$ easy_install django_userlog_0.1.tar.gz
}}}

=== Configuration ===

==== Adding the userlog app ====

Add //userlog// and //south// (if you aren't using South already) to your //settings.INSTALLED_APPS//:

{{{
INSTALLED_APPS = (
...
    'south',
    'userlog',
)
}}}

You will run ''syncdb'' to create the South tables and then ''migrate userlog'' to create/migrate the Userlog DB schema. Ex:

{{{
$ ./manage.py syncdb
$ ./manage.py migrate userlog
}}}

==== Changes in settings.py ====

Add //userlog.middleware.RequestToThreadLocalMiddleware// to //settings.MIDDLEWARE_CLASSES//:

{{{
MIDDLEWARE_CLASSES = (
    'userlog.middleware.RequestToThreadLocalMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
...
)
}}}

Add //userlog.backend.AuthFailedLoggerBackend// to  //settings.AUTHENTICATION_BACKENDS// **as the last element**:

{{{
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'userlog.backend.AuthFailedLoggerBackend'
)
}}}

==== Enabling the admin site for userlog ====

In order to see the logs you will have to enable Django Admin at least for the userlog application.

Head to the admin page of your project and see the logs "Failed login log" and "Login log" under the Userlog app.

=== Done ===

Userlog is set up and will log all log in attempts for your project.

In case you would like to know the technical details please go to the [[how it works]] page.

For developer specific information you probably also want to read the [[development]] page.

New releases will be announced on the [[Releases]] page.
