# -*- coding: utf-8 -*-
"""
Basic wire operations with the API - GET/POST/PUT.

This is a simple wrapper around requests.

"""
import logging
import requests
import urlparse

from django_onfido import settings

logger = logging.getLogger(__name__)


class ApiError(Exception):

    """Error raised when interacting with the API."""

    def __init__(self, response):
        """Initialise error from response object."""
        data = response.json()
        super(ApiError, self).__init__(data['error']['message'])
        self.error_type = data['error']['type']


def url(path):
    """Format absolute API URL."""
    return urlparse.urljoin(settings.ONFIDO_API_ROOT, path)


def _headers(api_key=settings.ONFIDO_API_KEY):
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


def get(url):
    """Make a GET request and return the response as JSON."""
    logger.debug("Making request to %s", url)
    return _respond(requests.get(url, headers=_headers()))


def post(url, data):
    """Make a POST request and return the response as JSON."""
    return _respond(requests.post(url, headers=_headers(), json=data))
