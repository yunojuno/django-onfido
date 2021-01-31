"""Full integration test - do not run in CI."""
from copy import deepcopy
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from onfido.helpers import create_applicant, create_check
from onfido.models import Event, Report

from .conftest import (
    TEST_APPLICANT,
    TEST_CHECK,
    TEST_EVENT,
    TEST_REPORT_IDENTITY_ENHANCED,
)

User = get_user_model()


@mock.patch("onfido.helpers.post")
@mock.patch("onfido.helpers.get")
@mock.patch("onfido.models.base.get")
@pytest.mark.django_db
def test_end_to_end(mock_fetch, mock_get, mock_post, user, client: Client):

    # Create a new applicant from the default user -
    # the API POST returns the TEST_APPLICANT JSON
    mock_post.return_value = deepcopy(TEST_APPLICANT)
    applicant = create_applicant(user)

    # Create a new check for the applicant just created
    # the API POST returns the new check (TEST_CHECK)
    # the API GET retrievs the reports for the check (TEST_REPORT_IDENTITY_ENHANCED)
    mock_post.return_value = TEST_CHECK
    mock_get.return_value = dict(reports=[TEST_REPORT_IDENTITY_ENHANCED])
    check = create_check(applicant, report_names=[Report.ReportType.IDENTITY_ENHANCED])
    assert not check.is_clear
    assert check.status == "in_progress"

    # this simulates a check.fetch() using the default JSON updated
    # with the contents from the event - we are forcing the result here
    # so that the check comes back from the fetch() as "complete" and "clear"
    check.refresh_from_db()
    mock_fetch.return_value = check.raw
    mock_fetch.return_value["status"] = "complete"
    mock_fetch.return_value["result"] = "clear"

    # Call the status_update webhook with the TEST_EVENT payload
    url = reverse("onfido:status_update")
    with mock.patch("onfido.decorators.TEST_MODE", True):
        client.post(url, data=TEST_EVENT, content_type="application/json")
    assert mock_fetch.call_count == 1
    assert Event.objects.count() == 1
    check.refresh_from_db()
    assert check.is_clear
    assert check.status == "complete"
