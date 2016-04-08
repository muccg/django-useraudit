# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('useraudit', '0002_loginattempt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loginattempt',
            name='count',
            field=models.PositiveIntegerField(default=0, null=True, blank=True),
        ),
    ]
