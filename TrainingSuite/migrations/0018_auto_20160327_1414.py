# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-27 11:14
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('TrainingSuite', '0017_auto_20160327_1413'),
    ]

    operations = [
        migrations.RenameField(
            model_name='session',
            old_name='description',
            new_name='short_description',
        ),
    ]