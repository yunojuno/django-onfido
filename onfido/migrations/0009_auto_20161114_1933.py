# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('onfido', '0008_auto_20161028_0815'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='onfido_id',
            field=models.CharField(help_text='The Onfido ID of the related resource.', max_length=40, verbose_name=b'Onfido ID'),
        ),
        migrations.RenameField(
            model_name='event',
            old_name='created_at',
            new_name='completed_at',
        ),
    ]
