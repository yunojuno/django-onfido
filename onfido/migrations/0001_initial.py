# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Applicant",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "onfido_id",
                    models.CharField(
                        help_text="The id returned from the Onfido API.",
                        unique=True,
                        max_length=40,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        help_text="The timestamp returned from the Onfido API.",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "raw",
                    models.TextField(
                        default="{}",
                        help_text="The raw JSON returned from the API.",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        related_name="onfido_applicant",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                        help_text="Django user that maps to this applicant.",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Check",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "onfido_id",
                    models.CharField(
                        help_text="The id returned from the Onfido API.",
                        unique=True,
                        max_length=40,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        help_text="The timestamp returned from the Onfido API.",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "raw",
                    models.TextField(
                        default="{}",
                        help_text="The raw JSON returned from the API.",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        max_length=20,
                        null=True,
                        help_text="The current state of the check / report (from API).",
                        choices=[
                            (
                                "Check",
                                (
                                    ("in_progress", "In progress"),
                                    ("awaiting_applicant", "Awaiting applicant"),
                                    ("complete", "Complete"),
                                    ("withdrawn", "Withdrawn"),
                                    ("paused", "Paused"),
                                    ("reopened", "Reopened"),
                                ),
                            ),
                            (
                                "Report",
                                (
                                    ("awaiting_data", "Awaiting data"),
                                    ("awaiting_approval", "Awaiting approval"),
                                    ("complete", "Complete"),
                                    ("withdrawn", "Withdrawn"),
                                    ("paused", "Paused"),
                                    ("cancelled", "Cancelled"),
                                ),
                            ),
                        ],
                    ),
                ),
                (
                    "result",
                    models.CharField(
                        blank=True,
                        max_length=20,
                        null=True,
                        help_text="The final result of the check / reports (from API).",
                        choices=[
                            ("Check", (("clear", "Clear"), ("consider", "Consider"))),
                            (
                                "Report",
                                (
                                    ("clear", "Clear"),
                                    ("consider", "Consider"),
                                    ("unidentified", "Unidentified"),
                                ),
                            ),
                        ],
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        help_text="The timestamp of the most recent status change (from API).",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "check_type",
                    models.CharField(
                        help_text="See https://documentation.onfido.com/#check-types",
                        max_length=10,
                        choices=[
                            ("express", "Express check"),
                            ("standard", "Standard check"),
                        ],
                    ),
                ),
                (
                    "applicant",
                    models.ForeignKey(
                        related_name="checks",
                        to="onfido.Applicant",
                        on_delete=models.CASCADE,
                        help_text="The applicant for whom the check is being made.",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        related_name="onfido_checks",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                        help_text="The Django user (denormalised from Applicant to make navigation easier).",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Report",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "onfido_id",
                    models.CharField(
                        help_text="The id returned from the Onfido API.",
                        unique=True,
                        max_length=40,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        help_text="The timestamp returned from the Onfido API.",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "raw",
                    models.TextField(
                        default="{}",
                        help_text="The raw JSON returned from the API.",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        max_length=20,
                        null=True,
                        help_text="The current state of the check / report (from API).",
                        choices=[
                            (
                                "Check",
                                (
                                    ("in_progress", "In progress"),
                                    ("awaiting_applicant", "Awaiting applicant"),
                                    ("complete", "Complete"),
                                    ("withdrawn", "Withdrawn"),
                                    ("paused", "Paused"),
                                    ("reopened", "Reopened"),
                                ),
                            ),
                            (
                                "Report",
                                (
                                    ("awaiting_data", "Awaiting data"),
                                    ("awaiting_approval", "Awaiting approval"),
                                    ("complete", "Complete"),
                                    ("withdrawn", "Withdrawn"),
                                    ("paused", "Paused"),
                                    ("cancelled", "Cancelled"),
                                ),
                            ),
                        ],
                    ),
                ),
                (
                    "result",
                    models.CharField(
                        blank=True,
                        max_length=20,
                        null=True,
                        help_text="The final result of the check / reports (from API).",
                        choices=[
                            ("Check", (("clear", "Clear"), ("consider", "Consider"))),
                            (
                                "Report",
                                (
                                    ("clear", "Clear"),
                                    ("consider", "Consider"),
                                    ("unidentified", "Unidentified"),
                                ),
                            ),
                        ],
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        help_text="The timestamp of the most recent status change (from API).",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "report_type",
                    models.CharField(
                        help_text="The name of the report - see https://documentation.onfido.com/#reports",
                        max_length=20,
                        choices=[
                            ("identity", "Identity report"),
                            ("document", "Document report"),
                            ("street_level", "Street level report"),
                            ("facial_similarity", "Facial similarity report"),
                            ("credit", "Credit report"),
                            ("criminal_history", "Criminal history"),
                            ("right_to_work", "Right to work"),
                            ("ssn_trace", "SSN trace"),
                        ],
                    ),
                ),
                (
                    "onfido_check",
                    models.ForeignKey(
                        related_name="reports",
                        to="onfido.Check",
                        on_delete=models.CASCADE,
                        help_text="Check to which this report is attached.",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        related_name="onfido_reports",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                        help_text="The Django user (denormalised from Applicant to make navigation easier).",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
