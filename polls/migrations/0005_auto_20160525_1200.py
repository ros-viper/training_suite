# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-25 09:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0004_auto_20160525_1155'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submittedresult',
            name='custom_options',
        ),
        migrations.AddField(
            model_name='submittedresult',
            name='custom_options',
            field=models.ManyToManyField(blank=True, null=True, to='polls.UserOption'),
        ),
        migrations.RemoveField(
            model_name='submittedresult',
            name='options',
        ),
        migrations.AddField(
            model_name='submittedresult',
            name='options',
            field=models.ManyToManyField(blank=True, null=True, to='polls.Option'),
        ),
    ]
