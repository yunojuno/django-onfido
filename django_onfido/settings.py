# -*- coding: utf-8 -*-
"""django_onfido settings."""
from os import getenv

from django.conf import settings

# read the api key in from settings, fall back to environment
ONFIDO_API_KEY = getattr(settings, 'ONFIDO_API_KEY', None) or getenv('ONFIDO_API_KEY')

# the API HTTP root url
ONFIDO_API_ROOT = "https://api.onfido.com/v2/"
