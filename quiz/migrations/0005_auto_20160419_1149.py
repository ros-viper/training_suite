# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-19 08:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0004_auto_20160418_1246'),
    ]

    operations = [
        migrations.AddField(
            model_name='submittedresult',
            name='questions_passed',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='test_length',
            field=models.IntegerField(default=5),
        ),
        migrations.AlterField(
            model_name='submittedresult',
            name='score',
            field=models.IntegerField(default=0),
        ),
    ]
