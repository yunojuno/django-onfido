# -*- coding: utf-8 -*-
"""
Basic wire operations with the API - GET/POST/PUT.

This is a simple wrapper around requests.

"""
import logging
import urlparse

import requests

from .settings import (
    API_ROOT,
    API_KEY
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
    return urlparse.urljoin(API_ROOT, path)


def _headers(api_key=API_KEY):
    """Format request headers."""
    return {
        "Authorization": "Token token={0}".format(api_key),
        "Content-Type": "application/json"
    }


def _respond(response):
    """Process common response object."""
    if not str(response.status_code).startswith('2'):
        raise ApiError(response)
    data = response.json()
    logger.debug("Onfido API response: %s", data)
    return data


def get(href):
    """Make a GET request and return the response as JSON."""
    logger.debug("Onfido API GET request: %s", href)
    return _respond(requests.get(_url(href), headers=_headers()))


def post(href, data):
    """Make a POST request and return the response as JSON."""
    logger.debug("Onfido API POST request: %s: %s", href, data)
    return _respond(requests.post(_url(href), headers=_headers(), json=data))
