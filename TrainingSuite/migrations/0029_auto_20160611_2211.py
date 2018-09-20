# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-06-11 19:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TrainingSuite', '0028_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='content',
            field=models.CharField(default='', max_length=200),
        ),
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('session', 'New session is available'), ('resource', 'New resource is available'), ('task', 'Task is assigned/updated'), ('comment', 'New reply on solution'), ('solution', 'New solution submitted'), ('discussion_thread', 'New discussion started'), ('discussion_update', 'New message in discussion'), ('general', 'Notification')], default='general', max_length=30),
        ),
    ]
