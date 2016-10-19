# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('onfido', '0002_auto_20161019_1037'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicant',
            name='user',
            field=models.OneToOneField(related_name='onfido_applicant', to=settings.AUTH_USER_MODEL, help_text='Django user that maps to this applicant.'),
        ),
    ]
