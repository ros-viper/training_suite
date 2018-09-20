# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-09-20 11:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('TrainingSuite', '0030_auto_20160919_0937'),
    ]

    operations = [
        migrations.CreateModel(
            name='Slides_to_Sessions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='TrainingSuite.Session')),
            ],
        ),
        migrations.CreateModel(
            name='Slideshow',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.URLField(blank=True, null=True)),
                ('name', models.CharField(max_length=100)),
                ('comment', models.CharField(blank=True, max_length=100)),
                ('sessions', models.ManyToManyField(blank=True, null=True, through='TrainingSuite.Slides_to_Sessions', to='TrainingSuite.Session')),
            ],
        ),
        migrations.AddField(
            model_name='slides_to_sessions',
            name='slideshow',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='TrainingSuite.Slideshow'),
        ),
    ]
