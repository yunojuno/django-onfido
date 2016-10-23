# -*- coding: utf-8 -*-
"""onfido settings."""
from os import getenv

from django.conf import settings

# read the api key in from settings, fall back to environment
API_KEY = getattr(settings, 'ONFIDO_API_KEY', None) or getenv('ONFIDO_API_KEY')

# the API HTTP root url
API_ROOT = "https://api.onfido.com/v2/"

LOG_EVENTS = (
    getattr(settings, 'ONFIDO_LOG_EVENTS', False) or
    getenv('ONFIDO_LOG_EVENTS', False)
)
