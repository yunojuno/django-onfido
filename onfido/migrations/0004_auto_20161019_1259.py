# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import onfido.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('onfido', '0003_auto_20161019_1038'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicant',
            name='raw',
            field=onfido.db.fields.JSONField(default=b'{}', help_text='The raw JSON returned from the API.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='check',
            name='raw',
            field=onfido.db.fields.JSONField(default=b'{}', help_text='The raw JSON returned from the API.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='raw',
            field=onfido.db.fields.JSONField(default=b'{}', help_text='The raw JSON returned from the API.', null=True, blank=True),
        ),
    ]
