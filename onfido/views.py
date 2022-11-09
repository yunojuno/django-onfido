"""onfido views.

The Onfido views are mainly callback handlers for the updates
in status' of checks and reports.

See https://documentation.onfido.com/?shell#webhooks

"""
from __future__ import annotations

import json
import logging

from django.http import HttpRequest, HttpResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt

from .decorators import verify_signature
from .models import Check, Event, Report
from .settings import LOG_EVENTS

logger = logging.getLogger(__name__)


@csrf_exempt
@verify_signature()
def status_update(request: HttpRequest) -> HttpResponse:
    """
    Handle event callbacks from the API.

    This is the request handler which does little other than
    log the request and call the _webhook function which does
    the processing. Done like this to make it easier to test
    without having to set up request objects.

    NB This view function will always return a 200 status -
    in order to prevent Onfido from endlessly retrying. The
    only exceptions to this are caused by the verify_signature
    decorator - if it cannot verify the callback, then it will
    return a 403 - which should be ok, as if Onfido sends the
    request it should never fail...

    """
    received_at = now()
    logger.debug("Received Onfido callback: %s", request.body)
    data = json.loads(request.body)
    event = Event(received_at=received_at)
    try:
        resource = event.parse(data).resource
        resource.update_status(event)
        if LOG_EVENTS:
            event.save()
        return HttpResponse("Update processed.")
    except KeyError as ex:
        logger.warning("Missing Onfido event content.", exc_info=ex)
        return HttpResponse("Unexpected event content.")
    except ValueError:
        logger.warning("Unknown Onfido resource type: %s", event.resource_type)
        return HttpResponse("Unknown resource type.")
    except Check.DoesNotExist:
        logger.warning("Onfido check does not exist: %s", event.onfido_id)
        return HttpResponse("Check not found.")
    except Report.DoesNotExist:
        logger.warning("Onfido report does not exist: %s", event.onfido_id)
        return HttpResponse("Report not found.")
    except Exception:  # noqa: B902
        logger.exception("Onfido update could not be processed.")
        return HttpResponse("Unknown error.")
