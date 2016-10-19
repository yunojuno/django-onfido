# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('onfido', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicant',
            name='created_at',
            field=models.DateTimeField(help_text='The timestamp returned from the Onfido API.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='check',
            name='created_at',
            field=models.DateTimeField(help_text='The timestamp returned from the Onfido API.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='check',
            name='result',
            field=models.CharField(blank=True, max_length=20, null=True, help_text='The final result of the check / reports (from API).', choices=[(b'Check', ((b'clear', b'Clear'), (b'consider', b'Consider'))), (b'Report', ((b'clear', b'Clear'), (b'consider', b'Consider'), (b'unidentified', b'Unidentified')))]),
        ),
        migrations.AlterField(
            model_name='check',
            name='status',
            field=models.CharField(blank=True, max_length=20, null=True, help_text='The current state of the check / report (from API).', choices=[(b'Check', ((b'in_progress', b'In progress'), (b'awaiting_applicant', b'Awaiting applicant'), (b'complete', b'Complete'), (b'withdrawn', b'Withdrawn'), (b'paused', b'Paused'), (b'reopened', b'Reopened'))), (b'Report', ((b'awaiting_data', b'Awaiting data'), (b'awaiting_approval', b'Awaiting approval'), (b'complete', b'Complete'), (b'withdrawn', b'Withdrawn'), (b'paused', b'Paused'), (b'cancelled', b'Cancelled')))]),
        ),
        migrations.AlterField(
            model_name='check',
            name='updated_at',
            field=models.DateTimeField(help_text='The timestamp of the most recent status change (from API).', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='created_at',
            field=models.DateTimeField(help_text='The timestamp returned from the Onfido API.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='report_type',
            field=models.CharField(help_text='The name of the report - see https://documentation.onfido.com/#reports', max_length=20, choices=[(b'identity', b'Identity report'), (b'document', b'Document report'), (b'street_level', b'Street level report'), (b'facial_similarity', b'Facial similarity report')]),
        ),
        migrations.AlterField(
            model_name='report',
            name='result',
            field=models.CharField(blank=True, max_length=20, null=True, help_text='The final result of the check / reports (from API).', choices=[(b'Check', ((b'clear', b'Clear'), (b'consider', b'Consider'))), (b'Report', ((b'clear', b'Clear'), (b'consider', b'Consider'), (b'unidentified', b'Unidentified')))]),
        ),
        migrations.AlterField(
            model_name='report',
            name='status',
            field=models.CharField(blank=True, max_length=20, null=True, help_text='The current state of the check / report (from API).', choices=[(b'Check', ((b'in_progress', b'In progress'), (b'awaiting_applicant', b'Awaiting applicant'), (b'complete', b'Complete'), (b'withdrawn', b'Withdrawn'), (b'paused', b'Paused'), (b'reopened', b'Reopened'))), (b'Report', ((b'awaiting_data', b'Awaiting data'), (b'awaiting_approval', b'Awaiting approval'), (b'complete', b'Complete'), (b'withdrawn', b'Withdrawn'), (b'paused', b'Paused'), (b'cancelled', b'Cancelled')))]),
        ),
        migrations.AlterField(
            model_name='report',
            name='updated_at',
            field=models.DateTimeField(help_text='The timestamp of the most recent status change (from API).', null=True, blank=True),
        ),
    ]
