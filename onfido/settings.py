# -*- coding: utf-8 -*-
"""onfido settings."""
from os import getenv

from django.conf import settings

# read the api key in from settings, fall back to environment
API_KEY = getattr(settings, 'ONFIDO_API_KEY', None) or getenv('ONFIDO_API_KEY')

# the API HTTP root url
API_ROOT = "https://api.onfido.com/v2/"

# flag to turn event logging on/off
LOG_EVENTS = (
    getattr(settings, 'ONFIDO_LOG_EVENTS', False) or
    getenv('ONFIDO_LOG_EVENTS', False)
)

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
