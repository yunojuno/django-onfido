from __future__ import annotations

from typing import Any, Iterable

from django.conf import settings

from .api import post
from .models import Applicant, Check, Report


def create_applicant(user: settings.AUTH_USER_MODEL, **kwargs: Any) -> Applicant:
    """
    Create an applicant in the Onfido system.

    Args:
        user: a Django User instance to register as an applicant.
    Kwargs:
       any kwargs passed in are merged into the data dict sent to the API. This
       enables support for additional applicant properties - e.g dob, gender,
       country, and any others that may change over time.
       See https://documentation.onfido.com/#create-applicant for details.
    """
    data = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
    }
    data.update(kwargs)
    response = post("applicants", data)
    return Applicant.objects.create_applicant(user, response)


def create_check(
    applicant: Applicant, check_type: str, reports: Iterable, **kwargs: Any
) -> Check:
    """
    Create a new Check (and child Reports).

    Args:
        applicant: Applicant for whom the checks are being made.
        check_type: string, currently only 'standard' is supported.
        reports: list of strings, each of which is a valid report type.

    Kwargs:
        any kwargs passed in are merged into the data dict sent to the API. This
        enables support for additional check properties - e.g. redirect_uri,
        tags, suppress_form_emails and any other that may change over time. See
        https://documentation.onfido.com/#checks for details.

    Returns a new Check object, and creates the child Report objects.

    """
    if check_type != "standard":
        raise ValueError(
            f"Invalid check_type '{check_type}', currently only 'standard' "
            "checks are supported."
        )
    if not isinstance(reports, (list, tuple)):
        raise ValueError(
            f"Invalid reports arg '{reports}', must be a list or tuple " "if supplied."
        )
    data = {
        "type": check_type,
        "reports": [{"name": r} for r in reports],
    }
    # merge in the additional kwargs
    data.update(kwargs)
    response = post("applicants/{}/checks".format(applicant.onfido_id), data)
    check = Check.objects.create_check(applicant=applicant, raw=response)
    for report in response["reports"]:
        Report.objects.create_report(check=check, raw=report)
    return check
