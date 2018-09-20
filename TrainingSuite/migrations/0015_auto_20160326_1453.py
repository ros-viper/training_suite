# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-26 14:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TrainingSuite', '0014_auto_20160326_1140'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resource',
            name='session',
        ),
        migrations.AddField(
            model_name='resource',
            name='sessions',
            field=models.ManyToManyField(to='TrainingSuite.Session'),
        ),
    ]
