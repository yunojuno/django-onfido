# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Applicant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('onfido_id', models.CharField(help_text='The id returned from the Onfido API.', unique=True, max_length=40)),
                ('created_at', models.DateTimeField(help_text='The timestamp returned from the Onfido API.', null=True, blank=True)),
                ('raw', models.TextField(default=b'{}', help_text='The raw JSON returned from the API.', null=True, blank=True)),
                ('user', models.OneToOneField(related_name='onfido_applicant', to=settings.AUTH_USER_MODEL, help_text='Django user that maps to this applicant.')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Check',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('onfido_id', models.CharField(help_text='The id returned from the Onfido API.', unique=True, max_length=40)),
                ('created_at', models.DateTimeField(help_text='The timestamp returned from the Onfido API.', null=True, blank=True)),
                ('raw', models.TextField(default=b'{}', help_text='The raw JSON returned from the API.', null=True, blank=True)),
                ('status', models.CharField(blank=True, max_length=20, null=True, help_text='The current state of the check / report (from API).', choices=[(b'Check', ((b'in_progress', b'In progress'), (b'awaiting_applicant', b'Awaiting applicant'), (b'complete', b'Complete'), (b'withdrawn', b'Withdrawn'), (b'paused', b'Paused'), (b'reopened', b'Reopened'))), (b'Report', ((b'awaiting_data', b'Awaiting data'), (b'awaiting_approval', b'Awaiting approval'), (b'complete', b'Complete'), (b'withdrawn', b'Withdrawn'), (b'paused', b'Paused'), (b'cancelled', b'Cancelled')))])),
                ('result', models.CharField(blank=True, max_length=20, null=True, help_text='The final result of the check / reports (from API).', choices=[(b'Check', ((b'clear', b'Clear'), (b'consider', b'Consider'))), (b'Report', ((b'clear', b'Clear'), (b'consider', b'Consider'), (b'unidentified', b'Unidentified')))])),
                ('updated_at', models.DateTimeField(help_text='The timestamp of the most recent status change (from API).', null=True, blank=True)),
                ('check_type', models.CharField(help_text='See https://documentation.onfido.com/#check-types', max_length=10, choices=[(b'express', b'Express check'), (b'standard', b'Standard check')])),
                ('applicant', models.ForeignKey(related_name='checks', to='onfido.Applicant', help_text='The applicant for whom the check is being made.')),
                ('user', models.ForeignKey(related_name='onfido_checks', to=settings.AUTH_USER_MODEL, help_text='The Django user (denormalised from Applicant to make navigation easier).')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('onfido_id', models.CharField(help_text='The id returned from the Onfido API.', unique=True, max_length=40)),
                ('created_at', models.DateTimeField(help_text='The timestamp returned from the Onfido API.', null=True, blank=True)),
                ('raw', models.TextField(default=b'{}', help_text='The raw JSON returned from the API.', null=True, blank=True)),
                ('status', models.CharField(blank=True, max_length=20, null=True, help_text='The current state of the check / report (from API).', choices=[(b'Check', ((b'in_progress', b'In progress'), (b'awaiting_applicant', b'Awaiting applicant'), (b'complete', b'Complete'), (b'withdrawn', b'Withdrawn'), (b'paused', b'Paused'), (b'reopened', b'Reopened'))), (b'Report', ((b'awaiting_data', b'Awaiting data'), (b'awaiting_approval', b'Awaiting approval'), (b'complete', b'Complete'), (b'withdrawn', b'Withdrawn'), (b'paused', b'Paused'), (b'cancelled', b'Cancelled')))])),
                ('result', models.CharField(blank=True, max_length=20, null=True, help_text='The final result of the check / reports (from API).', choices=[(b'Check', ((b'clear', b'Clear'), (b'consider', b'Consider'))), (b'Report', ((b'clear', b'Clear'), (b'consider', b'Consider'), (b'unidentified', b'Unidentified')))])),
                ('updated_at', models.DateTimeField(help_text='The timestamp of the most recent status change (from API).', null=True, blank=True)),
                ('report_type', models.CharField(help_text='The name of the report - see https://documentation.onfido.com/#reports', max_length=20, choices=[(b'identity', b'Identity report'), (b'document', b'Document report'), (b'street_level', b'Street level report'), (b'facial_similarity', b'Facial similarity report'), (b'credit', b'Credit report'), (b'criminal_history', b'Criminal history'), (b'right_to_work', b'Right to work'), (b'ssn_trace', b'SSN trace')])),
                ('onfido_check', models.ForeignKey(related_name='reports', to='onfido.Check', help_text='Check to which this report is attached.')),
                ('user', models.ForeignKey(related_name='onfido_reports', to=settings.AUTH_USER_MODEL, help_text='The Django user (denormalised from Applicant to make navigation easier).')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
