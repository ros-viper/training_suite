# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-21 17:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TrainingSuite', '0008_task_default_solution'),
    ]

    operations = [
        migrations.AddField(
            model_name='solution',
            name='committed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]