# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-19 06:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0015_auto_20160519_0904'),
    ]

    operations = [
        migrations.AddField(
            model_name='submittedresult',
            name='passed_by_score',
            field=models.BooleanField(default=False),
        ),
    ]
