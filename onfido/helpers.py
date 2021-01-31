from __future__ import annotations

from typing import Any, Iterable

from django.conf import settings

from .api import get, post
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


def create_check(applicant: Applicant, report_names: Iterable, **kwargs: Any) -> Check:
    """
    Create a new Check (and child Reports).

    Args:
        applicant: Applicant for whom the checks are being made.
        report_names: list of strings, each of which is a valid report type.

    Kwargs:
        any kwargs passed in are merged into the data dict sent to the API. This
        enables support for additional check properties - e.g. redirect_uri,
        tags, suppress_form_emails and any other that may change over time. See
        https://documentation.onfido.com/#checks for details.

    Returns a new Check object, and creates the child Report objects.

    """
    data = {
        "applicant_id": applicant.onfido_id,
        "report_names": report_names,
    }
    # merge in the additional kwargs
    data.update(kwargs)
    response = post("checks", data)
    check = Check.objects.create_check(applicant=applicant, raw=response)
    reports = get(f"reports?check_id={check.onfido_id}")
    for report in reports["reports"]:
        Report.objects.create_report(check=check, raw=report)
    return check
