# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-27 11:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TrainingSuite', '0020_auto_20160327_1415'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='description',
            field=models.TextField(default='', max_length=3000),
        ),
    ]