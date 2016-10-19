# -*- coding: utf-8 -*-
import datetime
import json
import mock

import dateutil

from django.test import TestCase, RequestFactory

from ..models import Check, Report
from ..views import (
    status_update,
    _update_status,
    _get_manager
)


class ViewTests(TestCase):

    """Test for views module."""

    def test__get_manager(self):
        """Test the _get_manager function."""
        self.assertEqual(_get_manager('report'), Report.objects)
        self.assertEqual(_get_manager('check'), Check.objects)
        self.assertRaises(AssertionError, _get_manager, 'foo')

    def test__update_status(self):
        """Test the _status_update function."""
        # now mock out a real object, and check we're calling update_status
        with mock.patch.object(Check, 'objects') as mock_manager:
            obj = mock.Mock()
            mock_manager.get.return_value = obj
            _update_status("check", 'obj_id', 'action', 'status', 'completed_at')
            obj.update_status.assert_called_once_with('action', 'status', 'completed_at')

    def test_status_update(self):
        """Test the status_update view function."""
        data = {
            "payload": {
                "resource_type": "check",
                "action": "check.form_completed",
                "object": {
                    "id": "5345badd-f4bf-4240-9f3b-ffb998bda09e",
                    "status": "in_progress",
                    "completed_at": "2016-10-15 11:34:09 UTC",
                    "href": "https://api.onfido.com/v1/applicants/4d390bbd-63c7-4960-8304-a7a04a8051e8/checks/5345badd-f4bf-4240-9f3b-ffb998bda09e"  # noqa
                }
            }
        }
        factory = RequestFactory()

        def assert_update(data, message):
            request = factory.post('/', data=json.dumps(data), content_type='application/json')
            response = status_update(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, message)

        # invalid payload
        assert_update({}, 'Unexpected event content.')

        # invalid resource type
        data['payload']['resource_type'] = "foo"
        assert_update(data, 'Unknown resource type.')

        # unknown Check
        data['payload']['resource_type'] = "check"
        with mock.patch.object(Check, 'objects') as mock_manager:
            mock_manager.get.side_effect = Check.DoesNotExist()
            assert_update(data, 'Check not found.')

        # unknown Report
        data['payload']['resource_type'] = "report"
        with mock.patch.object(Report, 'objects') as mock_manager:
            mock_manager.get.side_effect = Report.DoesNotExist()
            assert_update(data, 'Report not found.')

        # unknown exception
        with mock.patch('onfido.views._update_status') as mock_update:
            mock_update.side_effect = Exception("foobar")
            assert_update(data, 'Unknown error.')

        # valid payload / object
        with mock.patch('onfido.views._update_status') as mock_manager:
            assert_update(data, 'Update processed.')

    @mock.patch('onfido.views._update_status')
    def test_date_format_bug(self, mock_update):
        """
        Test that we can cope with different date formats.

        The Onfido API uses different date formats - hence the use of
        python-dateutil to parse the strings they send us. This test
        just confirms that it's working properly.

        """
        factory = RequestFactory()

        def assert_dates(data):
            mock_update.reset_mock()
            request = factory.post('/', data=json.dumps(data), content_type='application/json')
            status_update(request)
            mock_update.assert_called_once_with(
                data['payload']['resource_type'],
                data['payload']['object']['id'],
                data['payload']['action'],
                data['payload']['object']['status'],
                # hard-code this one as we want to know we get exactly the same datetime
                datetime.datetime(2016, 10, 15, 11, 34, 9, tzinfo=dateutil.tz.tzlocal())
            )

        data = {
            "payload": {
                "resource_type": "check",
                "action": "check.form_completed",
                "object": {
                    "id": "5345badd-f4bf-4240-9f3b-ffb998bda09e",
                    "status": "in_progress",
                    "completed_at": "2016-10-15 11:34:09 UTC",
                    "href": "https://api.onfido.com/v1/applicants/4d390bbd-63c7-4960-8304-a7a04a8051e8/checks/5345badd-f4bf-4240-9f3b-ffb998bda09e"  # noqa
                }
            }
        }

        assert_dates(data)

        # different format, same assert
        data['payload']['object']['completed_at'] = "2016-10-15T11:34:09Z"
        assert_dates(data)
