# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("onfido", "0008_rename_event_created_at"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="event",
            options={"ordering": ["completed_at"]},
        ),
        migrations.AddField(
            model_name="check",
            name="is_clear",
            field=models.BooleanField(
                default=None,
                null=True,
                blank=True,
                help_text="True if the check / report is 'clear' (via API or manual override).",
            ),
        ),
        migrations.AddField(
            model_name="report",
            name="is_clear",
            field=models.BooleanField(
                default=None,
                null=True,
                blank=True,
                help_text="True if the check / report is 'clear' (via API or manual override).",
            ),
        ),
    ]
