# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-09-23 16:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TrainingSuite', '0032_auto_20160920_1909'),
    ]

    operations = [
        migrations.AddField(
            model_name='solution',
            name='favorited',
            field=models.BooleanField(default=False),
        ),
    ]