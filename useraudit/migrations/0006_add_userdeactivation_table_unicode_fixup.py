# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('useraudit', '0005_add_userdeactivation_table'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdeactivation',
            name='reason',
            field=models.CharField(null=True, max_length=2, blank=True, choices=[('AE', 'Account expired'), ('PE', 'Password expired'), ('FL', 'Too many failed login attemtps')]),
        ),
    ]
