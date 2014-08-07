#!/usr/bin/env python

try:
    from setuptools.core import setup
except ImportError:
    from distutils.core import setup

setup(
    name='django-userlog',
    version='2.0.0',
    description='A django apps to record user log in ip addresses and user agent',
    author='Tamas Szabo',
    url='https://bitbucket.org/ccgmurdoch/django-userlog',
    download_url='https://bitbucket.org/ccgmurdoch/django-userlog/downloads',
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
        'userlog',
    ],
    package_data={
        'userlog': [
            'migrations/*'
        ]
    }
)
