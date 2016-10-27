# -*- coding: utf-8 -*-
import mock

from django.test import TestCase

from .. import settings


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
        data = {
            'foo': 'bar',
            'breakdown': {},
            'properties': {}
        }
        # default function should remove breakdown and properties
        data = settings.DEFAULT_REPORT_SCRUBBER(data)
        self.assertFalse('breakdown' in data)
        self.assertFalse('properties' in data)

    # mock scrubber that does nothing and returns the data unchanged
    @mock.patch('onfido.settings.scrub_report_data', lambda d: d)
    def test_override_report_scrubber(self):
        """Test the report_scrubber default function."""
        data = {
            'foo': 'bar',
            'breakdown': {},
            'properties': {}
        }
        # import here otherwise the mock is ineffective
        from ..settings import scrub_report_data
        # default function should remove breakdown and properties
        scrub_report_data(data)
        self.assertTrue('breakdown' in data)
        self.assertTrue('properties' in data)
