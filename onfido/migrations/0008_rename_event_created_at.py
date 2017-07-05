# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('onfido', '0007_rename_onfido_id_verbose_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='created_at',
            field=models.DateTimeField(help_text='The timestamp returned from the Onfido API.', null=True, blank=True),
        ),
        migrations.RenameField(
            model_name='event',
            old_name='created_at',
            new_name='completed_at',
        ),
    ]
