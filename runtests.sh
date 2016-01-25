#!/usr/bin/env sh

cd `dirname $0`

export PYTHONPATH=.
django-admin.py test --settings=useraudit.test_settings useraudit
EXIT1=$?
django-admin.py test --settings=useraudit_testapp.settings useraudit_testapp
EXIT2=$?

if [ $EXIT1 -ne 0 -o $EXIT2 -ne 0 ]; then
   exit 1
fi
