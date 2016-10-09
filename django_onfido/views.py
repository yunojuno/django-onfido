# -*- coding: utf-8 -*-
"""django_onfido views.

The Onfido views are mainly callback handlers for the updates
in status' of checks and reports.

See https://documentation.onfido.com/?shell#webhooks

"""
import json

from django_onfido.models import Check, Report


def handle_callback(request):
    """Handle event callbacks from the API."""
    data = json.loads(request.body)
    payload = data['payload']
    resource_type = payload['resource_type']
    if resource_type == 'report':
        return _handle_report_event(payload['action'], payload['object'])
    elif resource_type == 'check':
        return _handle_check_event(payload['action'], payload['object'])
    else:
        return


def _handle_check_event(action, data):
    """Handles a Check update."""
    check = Check.objects.get(id=data['id'])
    pass


def _handle_report_event(action, data):
    """Handles a Report update."""
    pass

