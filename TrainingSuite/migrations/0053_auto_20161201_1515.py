# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-12-01 13:15
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('TrainingSuite', '0052_auto_20161201_1426'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='resource',
            options={'ordering': ['sessions__order']},
        ),
    ]
