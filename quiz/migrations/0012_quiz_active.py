# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-10 07:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0011_auto_20160504_1133'),
    ]

    operations = [
        migrations.AddField(
            model_name='quiz',
            name='active',
            field=models.BooleanField(default=False),
        ),
    ]
