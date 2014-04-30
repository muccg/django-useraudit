#!/usr/bin/env python

try:
    from setuptools.core import setup
except ImportError:
    from distutils.core import setup

setup(
    name='django-userlog',
    version='0.2.2',
    description='A django apps to record user log in ip addresses and user agent',
    author='Tamas Szabo',
    url='https://bitbucket.org/ahunter_ccg/django-userlog',
    download_url='https://bitbucket.org/ahunter_ccg/django-userlog/downloads',
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
