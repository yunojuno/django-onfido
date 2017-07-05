# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onfido', '0002_event'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='action',
            field=models.CharField(help_text='The event name as returned from the API callback.', max_length=20),
        ),
    ]
