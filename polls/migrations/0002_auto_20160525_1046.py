# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-25 07:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='deadline',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='poll',
            name='deadline_active',
            field=models.BooleanField(default=False),
        ),
    ]