# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-13 12:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0013_quiztries'),
    ]

    operations = [
        migrations.AddField(
            model_name='quiz',
            name='retry_on_fail_enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='quiz',
            name='retry_on_pass_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='quiz',
            name='verbose_results_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
