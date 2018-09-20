# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-18 11:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TrainingSuite', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='course',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='comments',
            field=models.ManyToManyField(blank=True, to='TrainingSuite.Comment'),
        ),
        migrations.AlterField(
            model_name='student',
            name='courses',
            field=models.ManyToManyField(blank=True, to='TrainingSuite.Course'),
        ),
        migrations.AlterField(
            model_name='trainer',
            name='comments',
            field=models.ManyToManyField(blank=True, to='TrainingSuite.Comment'),
        ),
        migrations.AlterField(
            model_name='trainer',
            name='courses',
            field=models.ManyToManyField(blank=True, to='TrainingSuite.Course'),
        ),
    ]
