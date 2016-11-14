# -*- coding: utf-8 -*-
# Helper functions
from .api import post
from .models import (
    Applicant,
    Check,
    Report
)


def create_applicant(user, **kwargs):
    """Create an applicant in the Onfido system.

    Args:
        user: an auth.User instance to register as an applicant.
    Kwargs:
       any kwargs passed in are merged into the data dict sent to the API. This
       enables support for additional applicant properties - e.g dob, gender,
       country, and any others that may change over time.
       See https://documentation.onfido.com/#create-applicant for details.
    """
    data = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email
    }
    data.update(kwargs)
    response = post('applicants', data)
    return Applicant.objects.create_applicant(user, response)


def create_check(applicant, check_type, reports, **kwargs):
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
    assert check_type == 'standard', (
        "Invalid check_type '{}', currently only 'standard' "
        "checks are supported.".format(check_type)
    )
    assert isinstance(reports, (list, tuple)), (
        "Invalid reports arg '{}', must be a list or tuple "
        "if supplied.".format(reports)
    )
    data = {
        "type": check_type,
        "reports": [{'name': r} for r in reports],
    }
    # merge in the additional kwargs
    data.update(kwargs)
    response = post('applicants/{}/checks'.format(applicant.onfido_id), data)
    check = Check.objects.create_check(applicant=applicant, raw=response)
    for report in response['reports']:
        Report.objects.create_report(check=check, raw=report)
    return check
