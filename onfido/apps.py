# -*- coding: utf-8 -*-
from django.apps import AppConfig


class OnfidoAppConfig(AppConfig):

    """AppConfig for Django-Onfido."""

    name = 'onfido'
    verbose_name = "Onfido"
    configs = []

    def ready(self):
        """Validate config and connect signals."""
        super(OnfidoAppConfig, self).ready()
