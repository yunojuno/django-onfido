# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('onfido', '0004_auto_20161019_1259'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='report_type',
            field=models.CharField(help_text='The name of the report - see https://documentation.onfido.com/#reports', max_length=20, choices=[(b'identity', b'Identity report'), (b'document', b'Document report'), (b'street_level', b'Street level report'), (b'facial_similarity', b'Facial similarity report'), (b'credit', b'Credit report'), (b'criminal_history', b'Criminal history'), (b'right_to_work', b'Right to work'), (b'ssn_trace', b'SSN trace')]),
        ),
    ]
