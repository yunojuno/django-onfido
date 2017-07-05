# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('onfido', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resource_type', models.CharField(help_text='The resource_type returned from the API callback.', max_length=20)),
                ('onfido_id', models.CharField(help_text='The id returned from the Onfido API.', max_length=40)),
                ('action', models.CharField(help_text='The resource_type returned from the API callback.', max_length=20)),
                ('status_before', models.CharField(help_text='The status of the object before the event.', max_length=20)),
                ('status_after', models.CharField(help_text='The status of the object after the event.', max_length=20)),
                ('completed_at', models.DateTimeField(help_text='The completed_at timestamp returned from the API callback.')),
                ('user', models.ForeignKey(related_name='onfido_events', to=settings.AUTH_USER_MODEL, help_text='The user who triggered the event.')),
            ],
        ),
    ]
