# -*- coding: utf-8 -*-
import json
import mock

from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory

from ..models import (
    Applicant,
    Check,
    Report,
    Event,
)
from ..views import status_update


class ViewTests(TestCase):

    """onfido.views module tests."""

    @mock.patch('onfido.decorators.WEBHOOK_TOKEN')
    def test_status_update(self, *args):
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

        @mock.patch('onfido.decorators._match', lambda x, y: True)
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
        with mock.patch.object(Event, 'parse') as mock_parse:
            mock_parse.side_effect = Exception("foobar")
            assert_update(data, 'Unknown error.')

        # valid payload / object
        mock_check = mock.Mock(spec=Check)
        with mock.patch(
            'onfido.models.Event.resource',
            new_callable=mock.PropertyMock(return_value=mock_check)
        ):
            # mock_resource.return_value = mock_check
            assert_update(data, 'Update processed.')
            mock_check.update_status.assert_called_once()

        # now check that a good payload passes.
        data['payload']['resource_type'] = 'check'
        user = User.objects.create_user('fred')
        applicant = Applicant(user=user, onfido_id='foo').save()
        check = Check(user=user, applicant=applicant, check_type='standard')
        check.onfido_id = data['payload']['object']['id']
        check.save()

        # validate that the LOG_EVENTS setting is honoured
        with mock.patch.object(Event, 'save') as mock_save:

            with mock.patch('onfido.views.LOG_EVENTS', False):
                assert_update(data, 'Update processed.')
                mock_save.assert_not_called()

            # force creation of event
            with mock.patch('onfido.views.LOG_EVENTS', True):
                assert_update(data, 'Update processed.')
                mock_save.assert_called_once_with()
