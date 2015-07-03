# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FailedLoginLog',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('username', models.CharField(blank=True, null=True, max_length=255)),
                ('ip_address', models.CharField(blank=True, null=True, max_length=40, verbose_name='IP')),
                ('forwarded_by', models.CharField(blank=True, null=True, max_length=1000)),
                ('user_agent', models.CharField(blank=True, null=True, max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='LoginLog',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('username', models.CharField(blank=True, null=True, max_length=255)),
                ('ip_address', models.CharField(blank=True, null=True, max_length=40, verbose_name='IP')),
                ('forwarded_by', models.CharField(blank=True, null=True, max_length=1000)),
                ('user_agent', models.CharField(blank=True, null=True, max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
                'ordering': ['-timestamp'],
            },
        ),
    ]
