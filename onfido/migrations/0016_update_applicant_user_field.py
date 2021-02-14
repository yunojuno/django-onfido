# Generated by Django 3.1.6 on 2021-02-10 10:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("onfido", "0015_update_check_type_field"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="applicant",
            options={"ordering": ["created_at"]},
        ),
        migrations.AlterField(
            model_name="applicant",
            name="user",
            field=models.ForeignKey(
                help_text="Django user that maps to this applicant.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="onfido_applicants",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
