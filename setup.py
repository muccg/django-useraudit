#!/usr/bin/env python

try:
    from setuptools.core import setup
except ImportError:
    from distutils.core import setup

setup(
    name='django-useraudit',
    version='1.7.1',
    description='Django user audit utilities like logging user log in, disabling access when password expires or user is inactive',
    long_description='Django user audit utilities like logging user log in, disabling access when password expires or user is inactive',
    author='CCG, Murdoch University',
    author_email='devops@ccg.murdoch.edu.au',
    url='https://github.com/muccg/django-useraudit',
    download_url='https://github.com/muccg/django-useraudit/releases',
    classifiers=[
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development"
    ],
    zip_safe=False,
    packages=[
        'useraudit',
        'useraudit.migrations',
        'useraudit.management.commands',
    ],
    include_package_data=True,
)
