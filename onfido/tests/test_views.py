# -*- coding: utf-8 -*-
import json
import mock

from django.test import TestCase, Client, RequestFactory

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
            response = _update_status(
                "check", 'obj_id', 'action', 'status', 'completed_at'
            )
            obj.update_status.assert_called_once_with(
                'status', 'completed_at'
            )

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
                    "href": "https://api.onfido.com/v1/applicants/4d390bbd-63c7-4960-8304-a7a04a8051e8/checks/5345badd-f4bf-4240-9f3b-ffb998bda09e"
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
        with mock.patch('onfido.views._status_update') as mock_update:
            mock_update.side_effect = Exception("foobar")
            assert_update(data, 'Unknown error.')

        # valid payload / object
        with mock.patch('onfido.views._status_update') as mock_manager:
            request = factory.post('/', data=json.dumps(data), content_type='application/json')
            assert_update(data, 'Update processed.')
