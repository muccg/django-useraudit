# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('useraudit', '0003_auto_20160406_1434'),
    ]

    operations = [
        migrations.AlterField(
            model_name='failedloginlog',
            name='user_agent',
            field=models.CharField(max_length=1000, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='loginlog',
            name='user_agent',
            field=models.CharField(max_length=1000, null=True, blank=True),
        ),
    ]
