# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-25 10:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0005_auto_20160525_1200'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='verbose_results_enabled',
            field=models.BooleanField(default=True),
        ),
    ]
