# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('onfido', '0005_remove_event_user'),
    ]

    operations = [
        migrations.RenameField(
            model_name='event',
            old_name='completed_at',
            new_name='created_at',
        ),
        migrations.RenameField(
            model_name='event',
            old_name='resource_id',
            new_name='onfido_id'
        )
    ]
