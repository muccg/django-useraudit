#!/usr/bin/env sh

cd `dirname $0`

export PYTHONPATH=.
django-admin.py test --settings=userlog.test_settings userlog
django-admin.py test --settings=userlog_testapp.settings userlog_testapp
