# -*- coding: utf-8 -*-
"""
Basic wire operations with the API - GET/POST/PUT.

This is a simple wrapper around requests.

"""
import logging
import urlparse

import requests

from .models import (
    Applicant,
    Check,
    Report
)
from .settings import (
    ONFIDO_API_ROOT,
    ONFIDO_API_KEY
)

logger = logging.getLogger(__name__)


class ApiError(Exception):

    """Error raised when interacting with the API."""

    def __init__(self, response):
        """Initialise error from response object."""
        data = response.json()
        logger.debug("Onfido API error: {}".format(data))
        super(ApiError, self).__init__(data['error']['message'])
        self.error_type = data['error']['type']


def _url(path):
    """Format absolute API URL."""
    return urlparse.urljoin(ONFIDO_API_ROOT, path)


def _headers(api_key=ONFIDO_API_KEY):
    """Format request headers."""
    return {
        "Authorization": "Token token={0}".format(api_key),
        "Content-Type": "application/json"
    }


def _respond(response):
    """Process common response object."""
    logger.debug(response)
    if not str(response.status_code).startswith('2'):
        raise ApiError(response)
    return response.json()


def _get(url):
    """Make a GET request and return the response as JSON."""
    logger.debug("Making GET request to %s", url)
    return _respond(requests.get(url, headers=_headers()))


def _post(url, data):
    """Make a POST request and return the response as JSON."""
    logger.debug("Making POST request to %s", url)
    return _respond(requests.post(url, headers=_headers(), json=data))


def create_applicant(user):
    """Create an applicant in the Onfido system."""
    data = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email
    }
    response = _post(_url('applicants'), data)
    logger.debug(response)
    return Applicant.objects.create_applicant(user, response)


def create_check(
    applicant, check_type, reports,
    suppress_form_emails=True, redirect_uri=None
):
    """
    Create a new Check (and child Reports).

    Args:
        applicant: Applicant for whom the checks are being made.
        check_type: string, currently only 'standard' is supported.
        reports: list of strings, each of which is a valid report type.

    Kwargs:
        suppress_form_emails: bool, if True then suppress the email the Onfido
            itself would normally send when a check is initiated. Defaults to
            True.
        redirect_uri: string, a url to which to direct the user _after_ they
            have submitted all the information requested.

    Returns a new Check object, and creates the child Report objects.

    """
    data = {
        "type": check_type,
        "suppress_form_emails": suppress_form_emails,
        "reports": [{'name': r for r in reports}],
        "redirect_uri": redirect_uri
    }
    response = _post(_url('applicants/{}/checks'.format(applicant.id)), data)
    logger.debug(response)
    check = Check.objects.create_check(applicant=applicant, raw=response)
    for report in response['reports']:
        Report.objects.create_report(check=check, raw=report)
    return check
