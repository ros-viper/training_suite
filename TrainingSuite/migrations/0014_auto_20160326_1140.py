# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-26 11:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TrainingSuite', '0013_auto_20160326_1131'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='number',
            field=models.IntegerField(blank=True, default='1', null=True),
        ),
    ]
