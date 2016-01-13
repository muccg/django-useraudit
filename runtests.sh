#!/usr/bin/env sh

cd `dirname $0`

export PYTHONPATH=.
django-admin.py test --settings=userlog.test_settings userlog
EXIT1=$?
django-admin.py test --settings=userlog_testapp.settings userlog_testapp
EXIT2=$?

if [ $EXIT1 -ne 0 -o $EXIT2 -ne 0 ]; then
   exit 1
fi
