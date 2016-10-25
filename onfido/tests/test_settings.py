# -*- coding: utf-8 -*-
import mock

from django.test import TestCase, override_settings

from ..settings import DEFAULT_REPORT_SCRUBBER


class SettingsTests(TestCase):

    """settings module tests."""

    def test_default_report_scrubber(self):
        """Test the report_scrubber default function."""
        data = {
            'foo': 'bar',
            'breakdown': {},
            'properties': {}
        }
        # default function should remove breakdown and properties
        data = DEFAULT_REPORT_SCRUBBER(data)
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
