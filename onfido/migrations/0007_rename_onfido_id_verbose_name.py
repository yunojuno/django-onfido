# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('onfido', '0006_rename_event_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='onfido_id',
            field=models.CharField(help_text='The Onfido ID of the related resource.', max_length=40, verbose_name=b'Onfido ID'),
        ),
        migrations.AlterField(
            model_name='applicant',
            name='onfido_id',
            field=models.CharField(help_text='The id returned from the Onfido API.', unique=True, max_length=40, verbose_name=b'Onfido ID'),
        ),
        migrations.AlterField(
            model_name='check',
            name='onfido_id',
            field=models.CharField(help_text='The id returned from the Onfido API.', unique=True, max_length=40, verbose_name=b'Onfido ID'),
        ),
        migrations.AlterField(
            model_name='report',
            name='onfido_id',
            field=models.CharField(help_text='The id returned from the Onfido API.', unique=True, max_length=40, verbose_name=b'Onfido ID'),
        ),
    ]
