# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('useraudit', '0004_enlarge_user_agent_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserDeactivation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(max_length=255)),
                ('reason', models.CharField(blank=True, max_length=2, null=True, choices=[(b'AE', b'Account expired'), (b'PE', b'Password expired'), (b'FL', b'Too many failed login attemtps')])),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
