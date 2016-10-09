# -*- coding: utf-8 -*-
"""django-onfido apps module."""
from django.apps import AppConfig
# from django.core.exceptions import ImproperlyConfigured
# from django.db.models import signals


class OnfidoAppConfig(AppConfig):

    """AppConfig for Django-Onfido."""

    name = 'django_onfido'
    verbose_name = "Onfido"
    configs = []

    def ready(self):
        """Validate config and connect signals."""
        super(OnfidoAppConfig, self).ready()
