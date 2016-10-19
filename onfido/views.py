# -*- coding: utf-8 -*-
"""onfido views.

The Onfido views are mainly callback handlers for the updates
in status' of checks and reports.

See https://documentation.onfido.com/?shell#webhooks

"""
import json
import logging

from dateutil.parser import parse as date_parse

from django.http import HttpResponse

from .models import Check, Report

logger = logging.getLogger(__name__)


def status_update(request):
    """
    Handle event callbacks from the API.

    This is the request handler which does little other than
    log the request and call the _webhook function which does
    the processing. Done like this to make it easier to test
    without having to set up request objects.

    NB This view function will always return a 200 status -
    in order to prevent Onfido from endlessly retrying.

    """
    logger.debug("Received Onfido callback: {}".format(request.body))
    data = json.loads(request.body)
    try:
        payload = data['payload']
        resource_type = payload['resource_type']
        action = payload['action']
        obj = payload['object']
        obj_id = obj['id']
        obj_status = obj['status']
        obj_completed = date_parse(obj['completed_at'])
        _update_status(resource_type, obj_id, action, obj_status, obj_completed)
        return HttpResponse("Update processed.")
    except KeyError as ex:
        logger.warn("Missing Onfido event content: %s", ex)
        return HttpResponse("Unexpected event content.")
    except AssertionError:
        logger.warn("Unknown Onfido resource type: %s", resource_type)
        return HttpResponse("Unknown resource type.")
    except Check.DoesNotExist:
        logger.warn("Onfido check does not exist: %s", obj_id)
        return HttpResponse("Check not found.")
    except Report.DoesNotExist:
        logger.warn("Onfido report does not exist: %s", obj_id)
        return HttpResponse("Report not found.")
    except Exception:
        logger.exception("Onfido update could not be processed.")
        return HttpResponse("Unknown error.")


def _get_manager(resource_type):
    """Get appropriate model manager for a resource."""
    assert resource_type in ('report', 'check')
    return (
        Report.objects if resource_type == 'report'
        else Check.objects
    )


def _update_status(resource_type, obj_id, action, status, completed_at):
    """Process status update receive via webhook."""
    logger.debug("Processing '%s' action on %s.%s", action, resource_type, obj_id)
    manager = _get_manager(resource_type)
    obj = manager.get(id=obj_id)
    obj.update_status(action, status, completed_at)
