# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('onfido', '0003_auto_20161023_1455'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='onfido_id',
        ),
        migrations.RemoveField(
            model_name='event',
            name='status_after',
        ),
        migrations.RemoveField(
            model_name='event',
            name='status_before',
        ),
        migrations.AddField(
            model_name='event',
            name='raw',
            field=models.TextField(default=b'{}', help_text='The raw JSON returned from the API.', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='event',
            name='resource_id',
            field=models.CharField(default='', help_text='The Onfido id of the object that was updated, returned from the API.', max_length=40),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='status',
            field=models.CharField(default='', help_text='The status of the object after the event.', max_length=20),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='event',
            name='user',
            field=models.ForeignKey(related_name='onfido_events', blank=True, to=settings.AUTH_USER_MODEL, help_text='The user who triggered the event.', null=True),
        ),
    ]
