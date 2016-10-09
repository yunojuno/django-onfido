# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_onfido.db.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Applicant',
            fields=[
                ('id', models.CharField(help_text='The id returned from the Onfido API.', max_length=40, serialize=False, primary_key=True)),
                ('created_at', models.DateTimeField(help_text='The timestamp returned from the Onfido API.')),
                ('raw', django_onfido.db.fields.JSONField(default=b'{}', help_text='The raw JSON returned from the API.')),
                ('user', models.ForeignKey(help_text='Django user that maps to this applicant.', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Check',
            fields=[
                ('id', models.CharField(help_text='The id returned from the Onfido API.', max_length=40, serialize=False, primary_key=True)),
                ('created_at', models.DateTimeField(help_text='The timestamp returned from the Onfido API.')),
                ('raw', django_onfido.db.fields.JSONField(default=b'{}', help_text='The raw JSON returned from the API.')),
                ('check_type', models.CharField(help_text='See https://documentation.onfido.com/#check-types', max_length=10, choices=[(b'express', b'Express check'), (b'standard', b'Standard check')])),
                ('status', models.CharField(default=b'unknown', help_text='The current state of the check in the checking process.', max_length=20, choices=[(b'unknown', b'Unknown'), (b'in_progress', b'In progress'), (b'awaiting_applicant', b'Awaiting applicant'), (b'complete', b'Complete'), (b'withdrawn', b'Withdrawn'), (b'paused', b'Paused'), (b'reopened', b'Reopened')])),
                ('result', models.CharField(help_text='The overall result of the check (derived from reports).', max_length=20, blank=True)),
                ('applicant', models.ForeignKey(related_name='checks', to=settings.AUTH_USER_MODEL, help_text='The applicant for whom the check is being made.')),
                ('user', models.ForeignKey(related_name='onfido_checks', to=settings.AUTH_USER_MODEL, help_text='The Django user (denormalised from Applicant to make navigation easier).')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.CharField(help_text='The id returned from the Onfido API.', max_length=40, serialize=False, primary_key=True)),
                ('created_at', models.DateTimeField(help_text='The timestamp returned from the Onfido API.')),
                ('raw', django_onfido.db.fields.JSONField(default=b'{}', help_text='The raw JSON returned from the API.')),
                ('report_type', models.CharField(help_text='See https://documentation.onfido.com/#reports', max_length=20, choices=[(b'identity', b'Identity report'), (b'document', b'Document report'), (b'street_level', b'Street level report'), (b'facial_similarity', b'Facial similarity report')])),
                ('status', models.CharField(default=b'unknown', help_text='The current state of the report in the checking process.', max_length=20, choices=[(b'unknown', b'Unknown'), (b'awaiting_data', b'Awaiting data'), (b'awaiting_approval', b'Awaiting approval'), (b'complete', b'Complete'), (b'withdrawn', b'Withdrawn'), (b'paused', b'Paused'), (b'cancelled', b'Cancelled')])),
                ('result', models.CharField(help_text='The overall result of the report.', max_length=20, blank=True)),
                ('onfido_check', models.ForeignKey(related_name='reports', to='django_onfido.Check', help_text='Check to which this report is attached.')),
                ('user', models.ForeignKey(related_name='onfido_reports', to=settings.AUTH_USER_MODEL, help_text='The Django user (denormalised from Applicant to make navigation easier).')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
