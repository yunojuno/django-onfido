# -*- coding: utf-8 -*-
"""onfido settings."""
from os import getenv

from django.conf import settings

# the API HTTP root url
API_ROOT = "https://api.onfido.com/v2/"

# API key from evnironment by default
API_KEY = (
    getenv('ONFIDO_API_KEY', None) or
    getattr(settings, 'ONFIDO_API_KEY', None)
)

# Webhook token - see https://documentation.onfido.com/#webhooks
WEBHOOK_TOKEN = (
    getenv('ONFIDO_WEBHOOK_TOKEN', None) or
    getattr(settings, 'ONFIDO_WEBHOOK_TOKEN', None)
)

# Set to False to turn off event logging
LOG_EVENTS = getattr(settings, 'ONFIDO_LOG_EVENTS', True)

# Set to True to bypass request verification (NOT RECOMMENDED)
TEST_MODE = getattr(settings, 'ONFIDO_TEST_MODE', False)


def DEFAULT_REPORT_SCRUBBER(raw):
    """Default report scrubber, removes breakdown and properties."""
    try:
        del raw['breakdown']
        del raw['properties']
    except KeyError:
        pass
    return raw

# function used to scrub sensitive data from reports
scrub_report_data = (
    getattr(settings, 'ONFIDO_REPORT_SCRUBBER', None) or
    DEFAULT_REPORT_SCRUBBER
)
