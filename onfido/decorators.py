# -*- coding: utf-8 -*-
"""onfido views.

The Onfido views are mainly callback handlers for the updates
in status' of checks and reports.

See https://documentation.onfido.com/?shell#webhooks

"""
from functools import wraps
import hashlib
import hmac
import logging

from django.http import HttpResponseForbidden

from .settings import WEBHOOK_TOKEN


logger = logging.getLogger(__name__)


def _hmac(token, text):
    """Calculate SHA1 HMAC digest from request body and token."""
    return hmac.new(token, text, hashlib.sha1).hexdigest()


def _match(token, request):
    """
    Calculate signature and return True if it matches header.

    Args:
        token: string, the webhook_token. If None is passed in then the
            match is ignored. A warning will be logged.
        request: an HttpRequest object from which the body content and
            X-Signature header will be extracted and matched.

    Returns if there is a match.

    """
    try:
        return _hmac(token, request.body) == request.META['HTTP_X_SIGNATURE']
    except KeyError:
        logger.warn("Onfido callback missing X-Signature - this may be an unauthorised request.")
        return False
    except Exception:
        logger.exception("Onfido callback cannot be verified.")
        return False


def verify_signature():
    """
    View function decorator used to verify Onfido webhook signatures.

    This function uses the WEBHOOK_TOKEN specified in settings to calculate
    the HMAC. If it doesn't exist, then this decorator will immediately fail
    hard with an ImproperlyConfigure exception.

    See: https://documentation.onfido.com/#webhooks

        Each webhook URL is associated with a secret token. This is
        visible in the response.token field when registering a webhook.

        Events sent to your application will be signed using this token:
        verifying the request signature on your server prevents attackers
        from imitating valid webhooks. The HMAC digest signature, generated
        using SHA-1, will be stored in a X-Signature header.

        When you receive an event, you should compute a hash using your
        secret token, and ensure that the X-Signature sent by Onfido
        matches that hash.

    If the HMAC signatures don't match, return a 403

    """
    def decorator(func):
        @wraps(func)
        def _wrapped_func(request, *args, **kwargs):
            if _match(WEBHOOK_TOKEN, request):
                return func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden("Invalid X-Signature")
        return _wrapped_func
    return decorator
