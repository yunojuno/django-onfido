from unittest import mock

from django.test import TestCase

from onfido import settings


class SettingsTests(TestCase):

    """onfido.settings module tests."""

    def test_defaults(self):
        """Confirm the default settings exist."""
        self.assertEqual(settings.API_ROOT, "https://api.onfido.com/v2/")
        self.assertEqual(settings.API_KEY, None)
        self.assertEqual(settings.LOG_EVENTS, True)
        self.assertEqual(settings.WEBHOOK_TOKEN, None)
        self.assertEqual(settings.TEST_MODE, False)

    def test_default_report_scrubber(self):
        """Test the report_scrubber default function."""
        data = {"foo": "bar", "breakdown": {}, "properties": {}}
        # default function should remove breakdown and properties
        data = settings.DEFAULT_REPORT_SCRUBBER(data)
        self.assertFalse("breakdown" in data)
        self.assertFalse("properties" in data)

    # mock scrubber that does nothing and returns the data unchanged
    @mock.patch("onfido.settings.scrub_report_data", lambda d: d)
    def test_override_report_scrubber(self):
        """Test the report_scrubber default function."""
        data = {"foo": "bar", "breakdown": {}, "properties": {}}
        # import here otherwise the mock is ineffective
        from onfido.settings import scrub_report_data

        # default function should remove breakdown and properties
        scrub_report_data(data)
        self.assertTrue("breakdown" in data)
        self.assertTrue("properties" in data)

    def test_default_applicant_scrubber(self):
        """Test the applicant_scrubber default function."""
        data = {
            "addresses": [],
            "country": "gbr",
            "country_of_birth": None,
            "created_at": "2017-05-03T13:12:17Z",
            "dob": None,
            "email": "foobar@example.com",
            "first_name": "Foo",
            "gender": None,
            "href": "/v2/applicants/1b0f8e99-da6b-4ca5-9580-eed99ff691cd",
            "id": "1b0f8e97-dc6b-4ca5-9580-eed99ff691cd",
            "id_numbers": [],
            "last_name": "Bar",
            "middle_name": None,
            "mobile": None,
            "mothers_maiden_name": None,
            "nationality": None,
            "previous_last_name": None,
            "sandbox": False,
            "telephone": None,
            "title": None,
            "town_of_birth": None,
        }
        clean = settings.DEFAULT_APPLICANT_SCRUBBER(data)
        self.assertEqual(
            clean,
            {
                "created_at": "2017-05-03T13:12:17Z",
                "href": "/v2/applicants/1b0f8e99-da6b-4ca5-9580-eed99ff691cd",
                "id": "1b0f8e97-dc6b-4ca5-9580-eed99ff691cd",
            },
        )
