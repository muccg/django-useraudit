#!/usr/bin/env sh

PYTHONPATH=. django-admin.py test --settings=userlog.test_settings userlog
