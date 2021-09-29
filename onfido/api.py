"""
Basic wire operations with the API - GET/POST/PUT.

This is a simple wrapper around requests.

"""
from __future__ import annotations

import logging
from urllib import parse as urlparse

import requests
from django.http import HttpResponse

from .settings import API_KEY

logger = logging.getLogger(__name__)

# the API HTTP root url
API_ROOT = "https://api.onfido.com/v3/"


class ApiError(Exception):
    """Error raised when interacting with the API."""

    def __init__(self, response: HttpResponse) -> None:
        """Initialise error from response object."""
        data = response.json()
        logger.debug("Onfido API error: {}".format(data))
        super().__init__(data["error"]["message"])
        self.error_type = data["error"]["type"]


def _url(path: str) -> str:
    """Format absolute API URL."""
    return urlparse.urljoin(API_ROOT, path)


def _headers(api_key: str = API_KEY) -> dict[str, str]:
    """Format request headers."""
    return {
        "Authorization": "Token token={}".format(api_key),
        "Content-Type": "application/json",
    }


def _respond(response: HttpResponse) -> dict:
    """Process common response object."""
    if not str(response.status_code).startswith("2"):
        raise ApiError(response)
    data = response.json()
    logger.debug("Onfido API response: %s", data)
    return data


def get(href: str) -> dict:
    """Make a GET request and return the response as JSON."""
    logger.debug("Onfido API GET request: %s", href)
    return _respond(requests.get(_url(href), headers=_headers()))


def post(href: str, data: dict) -> dict:
    """Make a POST request and return the response as JSON."""
    logger.debug("Onfido API POST request: %s: %s", href, data)
    return _respond(requests.post(_url(href), headers=_headers(), json=data))
