# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-15 11:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0002_auto_20160413_1306'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='number',
            field=models.IntegerField(default=10000000),
        ),
    ]
