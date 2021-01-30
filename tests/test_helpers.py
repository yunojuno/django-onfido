from copy import deepcopy
from unittest import mock

from dateutil.parser import parse as date_parse
from django.contrib.auth import get_user_model
from django.test import TestCase

from onfido.helpers import (  # import from helpers to deter possible dependency issues
    Applicant,
    Check,
    Report,
    create_applicant,
    create_check,
)

from .test_data import (
    TEST_APPLICANT,
    TEST_CHECK,
    TEST_REPORT_DOCUMENT,
    TEST_REPORT_IDENTITY_ENHANCED,
)


class HelperTests(TestCase):

    """onfido.helper module tests."""

    @mock.patch("onfido.helpers.post")
    def test_create_applicant(self, mock_post):
        """Test the create_applicant function."""
        data = deepcopy(TEST_APPLICANT)
        mock_post.return_value = data
        user = get_user_model().objects.create_user(
            username="fred",
            first_name="Fred",
            last_name="Flintstone",
            email="fred@flintstone.com",
        )
        applicant = create_applicant(user)
        mock_post.assert_called_once_with(
            "applicants",
            {
                "first_name": "Fred",
                "last_name": "Flintstone",
                "email": "fred@flintstone.com",
            },
        )
        self.assertEqual(applicant.onfido_id, data["id"])
        self.assertEqual(applicant.user, user)
        self.assertEqual(applicant.created_at, date_parse(data["created_at"]))

    @mock.patch("onfido.helpers.post")
    def test_create_applicant_with_custom_data(self, mock_post):
        """Test the create_applicant function with extra custom POST data."""
        data = deepcopy(TEST_APPLICANT)
        mock_post.return_value = data
        user = get_user_model().objects.create_user(
            username="fred",
            first_name="Fred",
            last_name="Flintstone",
            email="fred@flintstone.com",
        )
        create_applicant(user, country="GBR", dob="2016-01-01", gender="male")
        mock_post.assert_called_once_with(
            "applicants",
            {
                "first_name": "Fred",
                "last_name": "Flintstone",
                "email": "fred@flintstone.com",
                "gender": "male",
                "dob": "2016-01-01",
                "country": "GBR",
            },
        )

    @mock.patch("onfido.helpers.post")
    @mock.patch("onfido.helpers.get")
    def test_create_check(self, mock_get, mock_post):
        """Test the create_check function."""
        applicant_data = deepcopy(TEST_APPLICANT)
        mock_post.return_value = TEST_CHECK
        mock_get.return_value = [TEST_REPORT_DOCUMENT, TEST_REPORT_IDENTITY_ENHANCED]
        user = get_user_model().objects.create_user(
            username="fred",
            first_name="Fred",
            last_name="Flintstone",
            email="fred@flintstone.com",
        )
        applicant = Applicant.objects.create_applicant(user, applicant_data)

        # 1. use the defaults.
        check = create_check(
            applicant,
            report_names=[
                TEST_REPORT_DOCUMENT["name"],
                TEST_REPORT_IDENTITY_ENHANCED["name"],
            ],
        )
        mock_post.assert_called_once_with(
            "checks",
            {
                "applicant_id": applicant.onfido_id,
                "report_names": [
                    Report.ReportType.DOCUMENT.value,
                    Report.ReportType.IDENTITY_ENHANCED.value,
                ],
            },
        )
        self.assertEqual(Check.objects.get(), check)
        # check we have two reports, and that the raw field matches the JSON
        # and that the parse method has run
        self.assertEqual(Report.objects.count(), 2)
        # confirm that kwargs are merged in correctly
        check.delete()
        mock_post.reset_mock()
        check = create_check(
            applicant, report_names=[Report.ReportType.IDENTITY_ENHANCED], foo="bar"
        )
        mock_post.assert_called_once_with(
            "checks",
            {
                "applicant_id": applicant.onfido_id,
                "report_names": [Report.ReportType.IDENTITY_ENHANCED.value],
                "foo": "bar",
            },
        )
