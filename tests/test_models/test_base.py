import datetime
from unittest import mock

import pytest
from dateutil.parser import parse as date_parse
from django.contrib.auth import get_user_model
from django.db.models import Model, query
from django.test import TestCase
from django.utils.timezone import now as tz_now

from onfido.api import ApiError
from onfido.models import Applicant, Check, Event
from onfido.models.base import BaseModel, BaseStatusModel


class BaseModelInstance(BaseModel):

    base_href = "test_models"

    class Meta:
        managed = False
        app_label = "tmp"


class BaseStatusModelInstance(BaseStatusModel):
    class Meta:
        managed = False
        app_label = "tmp"


class BaseModelTests(TestCase):
    """onfido.models.BaseModel tests."""

    def test_defaults(self):
        obj = BaseModelInstance()
        self.assertEqual(obj.id, None)
        self.assertEqual(obj.onfido_id, "")
        self.assertEqual(obj.created_at, None)
        self.assertEqual(obj.raw, None)

    @mock.patch.object(BaseModel, "full_clean")
    @mock.patch.object(Model, "save")
    def test_save(self, mock_save, mock_clean):
        """Test that save method returns self."""
        obj = BaseModelInstance()
        self.assertEqual(obj.save(), obj)

    def test_href(self):
        """Test the href property."""
        obj = BaseModelInstance(onfido_id="123")
        self.assertEqual(obj.href, "test_models/123")

    def test_parse(self):
        """Test the parse method."""
        data = {
            "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
            "created_at": "2016-10-15T19:05:50Z",
            "status": "awaiting_applicant",
            "type": "standard",
            "result": "clear",
        }
        obj = BaseModelInstance().parse(data)
        self.assertEqual(obj.onfido_id, data["id"])
        self.assertEqual(obj.created_at, date_parse(data["created_at"]))

    @mock.patch.object(BaseModel, "save")
    @mock.patch("onfido.models.base.get")
    def test_fetch(self, mock_get, mock_save):
        """Test the fetch method calls the API."""
        data = {
            "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
            "created_at": "2016-10-15T19:05:50Z",
            "status": "awaiting_applicant",
            "type": "standard",
            "result": "clear",
            "href": "/",
        }
        mock_get.return_value = data
        obj = BaseModelInstance(raw={"href": "/"})
        obj.fetch()
        # check that it has update raw, but parsed the return value
        self.assertEqual(obj.raw, data)
        self.assertEqual(obj.onfido_id, data["id"])
        self.assertEqual(obj.created_at, date_parse(data["created_at"]))
        # check that it has **not** called the save method
        mock_save.assert_not_called()

        # check what happens if API fails
        obj = BaseModelInstance(raw={"href": "/"})
        response = mock.Mock()
        response.json.return_value = {
            "error": {
                "fields": {},
                "message": "Authorization error: please re-check your credentials",
                "type": "authorization_error",
            }
        }
        mock_get.side_effect = ApiError(response)
        self.assertRaises(ApiError, obj.pull)

    @mock.patch.object(BaseModel, "save")
    @mock.patch.object(BaseModel, "fetch")
    def test_pull(self, mock_fetch, mock_save):
        """Test the pull method calls fetch and save."""
        obj = BaseModelInstance(raw={"href": "/"})
        mock_fetch.return_value = obj
        obj.pull()
        # check that it has parsed the return value
        mock_fetch.assert_called_once_with()
        mock_save.assert_called_once_with()


@pytest.mark.django_db
class TestBaseQuerySet:

    # def create_applicant(self, username):
    #     """Create new Applicant and user."""
    #     data = {"id": username, "created_at": tz_now().isoformat()}
    #     user = get_user_model().objects.create_user(username)
    #     applicant = Applicant.objects.create_applicant(user, raw=data)
    #     return applicant

    @mock.patch.object(BaseModel, "fetch")
    def test_fetch(self, mock_fetch, applicant):
        Applicant.objects.all().fetch()
        assert mock_fetch.call_count == 1

    @mock.patch.object(BaseModel, "fetch")
    def test_fetch__empty(self, mock_fetch):
        Applicant.objects.all().fetch()
        assert mock_fetch.call_count == 0

    @mock.patch.object(BaseModel, "fetch")
    def test_fetch__error(self, mock_fetch, applicant):
        # check that an error doesn't blow up everything
        mock_fetch.side_effect = Exception("Something went wrong")
        Applicant.objects.all().fetch()
        assert mock_fetch.call_count == 1

    @mock.patch.object(BaseModel, "pull")
    def test_pull(self, mock_pull, applicant):
        Applicant.objects.all().pull()
        assert mock_pull.call_count == 1

    @mock.patch.object(BaseModel, "pull")
    def test_pull__empty(self, mock_pull):
        Applicant.objects.all().pull()
        assert mock_pull.call_count == 0

    @mock.patch.object(BaseModel, "pull")
    def test_pull__error(self, mock_pull, applicant):
        mock_pull.side_effect = Exception("Something went wrong")
        Applicant.objects.all().pull()
        assert mock_pull.call_count == 1


class BaseStatusModelTests(TestCase):
    """onfido.models.BaseStatusModel tests."""

    def test_defaults(self):
        obj = BaseStatusModelInstance()
        self.assertEqual(obj.id, None)
        self.assertEqual(obj.onfido_id, "")
        self.assertEqual(obj.created_at, None)
        self.assertEqual(obj.status, None)
        self.assertEqual(obj.result, None)
        self.assertEqual(obj.updated_at, None)
        self.assertEqual(obj.raw, None)

    def test_parse(self):
        """Test the parse method."""
        data = {
            "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
            "created_at": "2016-10-15T19:05:50Z",
            "status": "awaiting_applicant",
            "type": "standard",
            "result": "clear",
        }
        obj = BaseStatusModelInstance().parse(data)
        self.assertEqual(obj.onfido_id, data["id"])
        self.assertEqual(obj.created_at, date_parse(data["created_at"]))
        self.assertEqual(obj.status, data["status"])
        self.assertEqual(obj.result, data["result"])

    @mock.patch("onfido.signals.on_status_change.send")
    @mock.patch("onfido.signals.on_completion.send")
    @mock.patch.object(BaseStatusModel, "pull")
    @mock.patch.object(BaseStatusModel, "save")
    def test_update_status(self, mock_save, mock_pull, mock_complete, mock_update):
        """Test the update_status method."""
        now = datetime.datetime.now()

        def reset():
            mock_save.reset_mock()
            mock_pull.reset_mock()
            mock_complete.reset_mock()
            mock_update.reset_mock()
            event = Event(
                action="form.opened",
                status="after",
                onfido_id="foo",
                resource_type="check",
                completed_at=now,
            )
            obj = BaseStatusModelInstance(status="before")
            assert obj.status == "before"
            assert obj.updated_at is None
            return event, obj

        # try passing in something that is not a datetime
        event, obj = reset()
        event.completed_at = None
        self.assertRaises(ValueError, obj.update_status, event)

        event, obj = reset()
        event.completed_at = now
        obj = obj.update_status(event)
        self.assertEqual(obj.status, event.status)
        self.assertEqual(obj.updated_at, now)
        mock_pull.assert_called_once_with()
        mock_save.assert_not_called()
        mock_update.assert_called_once_with(
            BaseStatusModelInstance,
            instance=obj,
            event=event.action,
            status_before="before",
            status_after=event.status,
        )
        mock_complete.assert_not_called()

        # if we send 'complete' as the status we should fire the second signal
        event, obj = reset()
        event.status = "complete"
        obj = obj.update_status(event)
        self.assertEqual(obj.status, event.status)
        self.assertEqual(obj.updated_at, now)
        mock_pull.assert_called_once_with()
        mock_save.assert_not_called()
        mock_update.assert_called_once_with(
            BaseStatusModelInstance,
            instance=obj,
            event=event.action,
            status_before="before",
            status_after=event.status,
        )
        mock_complete.assert_called_once_with(BaseStatusModelInstance, instance=obj)

        # test that we can handle the API failing on pull()
        event, obj = reset()
        mock_pull.side_effect = Exception("Something went wrong in the API")
        obj = obj.update_status(event)
        self.assertEqual(obj.status, event.status)
        self.assertEqual(obj.updated_at, now)
        mock_pull.assert_called_once_with()
        mock_save.assert_called_once_with()
        mock_update.assert_called_once_with(
            BaseStatusModelInstance,
            instance=obj,
            event=event.action,
            status_before="before",
            status_after=event.status,
        )
        mock_complete.assert_not_called()

    @mock.patch("onfido.models.base.tz_now")
    def test__override_event(self, mock_now):
        """Test the _override_event method."""
        now = datetime.datetime.now()
        mock_now.return_value = now
        data = {
            "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
            "created_at": "2016-10-15T19:05:50Z",
            "status": "awaiting_applicant",
            "type": "standard",
            "result": "clear",
            "href": "http://foo",
        }
        user = get_user_model()()
        obj = BaseStatusModelInstance().parse(data)
        event = obj._override_event(user)
        self.assertEqual(event.onfido_id, obj.onfido_id)
        self.assertEqual(event.action, "manual.override")
        self.assertEqual(event.resource_type, BaseStatusModelInstance._meta.model_name)
        self.assertEqual(event.status, obj.status)
        self.assertEqual(event.completed_at, now)

    @mock.patch.object(Event, "save")
    @mock.patch.object(BaseStatusModel, "save")
    def test_mark_as_clear(self, mock_save, mock_event_save):
        """Test the mark_as_clear method."""
        data = {
            "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
            "created_at": "2016-10-15T19:05:50Z",
            "status": "awaiting_applicant",
            "type": "standard",
            "result": None,
            "href": "http://foo",
        }
        user = get_user_model()()
        obj = Check().parse(data)
        self.assertIsNone(obj.is_clear)
        obj = obj.mark_as_clear(user)
        mock_save.assert_called_once_with()
        mock_event_save.assert_called_once_with()
        self.assertTrue(obj.is_clear)

    @mock.patch.object(query.QuerySet, "filter")
    def test_events(self, mock_filter):
        """Test the events method."""
        obj = BaseStatusModelInstance(onfido_id="foo")
        obj.events()
        mock_filter.assert_called_once_with(
            onfido_id="foo", resource_type="basestatusmodelinstance"
        )
