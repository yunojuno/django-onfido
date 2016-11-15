# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('onfido', '0009_auto_20161114_1933'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ['completed_at']},
        ),
        migrations.AddField(
            model_name='check',
            name='is_clear',
            field=models.NullBooleanField(default=None, help_text="True if the check / report is 'clear' (via API or manual override)."),
        ),
        migrations.AddField(
            model_name='report',
            name='is_clear',
            field=models.NullBooleanField(default=None, help_text="True if the check / report is 'clear' (via API or manual override)."),
        ),
    ]
