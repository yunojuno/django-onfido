from os import getenv

from django.conf import settings


def _setting(key, default):
    return getenv(key, default) or getattr(settings, key, default)


# API key from evnironment by default
API_KEY = _setting("ONFIDO_API_KEY", None)

# Webhook token - see https://documentation.onfido.com/#webhooks
WEBHOOK_TOKEN = _setting("ONFIDO_WEBHOOK_TOKEN", None)
# token must be a bytestring for HMAC function to work
WEBHOOK_TOKEN = str.encode(WEBHOOK_TOKEN) if WEBHOOK_TOKEN else None

# Set to False to turn off event logging
LOG_EVENTS = _setting("ONFIDO_LOG_EVENTS", True)

# Set to True to bypass request verification (NOT RECOMMENDED)
TEST_MODE = _setting("ONFIDO_TEST_MODE", False)


def DEFAULT_REPORT_SCRUBBER(raw):
    """Remove breakdown and properties."""
    return {k: v for k, v in raw.items() if k not in ("breakdown", "properties")}


def DEFAULT_APPLICANT_SCRUBBER(raw):
    """Remove all personal data."""
    return {k: v for k, v in raw.items() if k in ("id", "href", "created_at")}


# functions used to scrub sensitive data from reports
scrub_report_data = (
    getattr(settings, "ONFIDO_REPORT_SCRUBBER", None) or DEFAULT_REPORT_SCRUBBER
)

scrub_applicant_data = (
    getattr(settings, "ONFIDO_APPLICANT_SCRUBBER", None) or DEFAULT_APPLICANT_SCRUBBER
)
