# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-22 15:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('TrainingSuite', '0011_auto_20160321_1807'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['target_line', 'author_trainer', '-created_at']},
        ),
        migrations.AlterField(
            model_name='comment',
            name='author_student',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='TrainingSuite.Student'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='author_trainer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='TrainingSuite.Trainer'),
        ),
    ]