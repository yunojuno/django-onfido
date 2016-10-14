# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import onfido.db.fields
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
                ('raw', onfido.db.fields.JSONField(default=b'{}', help_text='The raw JSON returned from the API.')),
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
                ('raw', onfido.db.fields.JSONField(default=b'{}', help_text='The raw JSON returned from the API.')),
                ('status', models.CharField(default=b'unknown', help_text='The current state of the check / report (from API).', max_length=20)),
                ('result', models.CharField(default=b'unknown', help_text='The final result of the check / reports (from API).', max_length=20)),
                ('updated_at', models.DateTimeField(help_text='The timestamp of the most recent status change.', null=True, blank=True)),
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
                ('id', models.CharField(help_text='The id returned from the Onfido API.', max_length=40, serialize=False, primary_key=True)),
                ('created_at', models.DateTimeField(help_text='The timestamp returned from the Onfido API.')),
                ('raw', onfido.db.fields.JSONField(default=b'{}', help_text='The raw JSON returned from the API.')),
                ('status', models.CharField(default=b'unknown', help_text='The current state of the check / report (from API).', max_length=20)),
                ('result', models.CharField(default=b'unknown', help_text='The final result of the check / reports (from API).', max_length=20)),
                ('updated_at', models.DateTimeField(help_text='The timestamp of the most recent status change.', null=True, blank=True)),
                ('report_type', models.CharField(help_text='The name of the report - see https://documentation.onfido.com/#reports', max_length=20, choices=[(b'unknown', b'-'), (b'identity', b'Identity report'), (b'document', b'Document report'), (b'street_level', b'Street level report'), (b'facial_similarity', b'Facial similarity report')])),
                ('onfido_check', models.ForeignKey(related_name='reports', to='onfido.Check', help_text='Check to which this report is attached.')),
                ('user', models.ForeignKey(related_name='onfido_reports', to=settings.AUTH_USER_MODEL, help_text='The Django user (denormalised from Applicant to make navigation easier).')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
