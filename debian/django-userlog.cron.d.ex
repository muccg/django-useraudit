#
# Regular cron jobs for the django-userlog package
#
0 4	* * *	root	[ -x /usr/bin/django-userlog_maintenance ] && /usr/bin/django-userlog_maintenance
