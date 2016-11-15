# -*- coding: utf-8 -*-
import datetime
import mock

from dateutil.parser import parse as date_parse

from django.contrib.auth.models import User
from django.db.models import Model, query
from django.test import TestCase
from django.utils.timezone import now as tz_now

from ..api import ApiError
from ..models import (
    BaseModel,
    BaseQuerySet,
    BaseStatusModel,
    Applicant,
    Check,
    Report,
    Event,
    CheckQuerySet
)


class TestBaseModel(BaseModel):

    class Meta:
        managed = False


class TestBaseStatusModel(BaseStatusModel):

    class Meta:
        managed = False


class BaseModelTests(TestCase):

    """onfido.models.BaseModel tests."""

    def test_defaults(self):
        obj = TestBaseModel()
        self.assertEqual(obj.id, None)
        self.assertEqual(obj.onfido_id, '')
        self.assertEqual(obj.created_at, None)
        self.assertEqual(obj.raw, {})

    @mock.patch.object(BaseModel, 'full_clean')
    @mock.patch.object(Model, 'save')
    def test_save(self, mock_save, mock_clean):
        """Test that save method returns self."""
        obj = TestBaseModel()
        self.assertEqual(obj.save(), obj)

    def test_href(self):
        """Test the href property."""
        raw = {'href': 'foo'}
        obj = TestBaseModel(raw=raw)
        self.assertEqual(obj.href, raw['href'])

    def test_parse(self):
        """Test the parse method."""
        data = {
            "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
            "created_at": "2016-10-15T19:05:50Z",
            "status": "awaiting_applicant",
            "type": "standard",
            "result": "clear",
        }
        obj = TestBaseModel().parse(data)
        self.assertEqual(obj.onfido_id, data['id'])
        self.assertEqual(obj.created_at, date_parse(data['created_at']))

    @mock.patch.object(BaseModel, 'save')
    @mock.patch('onfido.models.get')
    def test_fetch(self, mock_get, mock_save):
        """Test the fetch method calls the API."""
        data = {
            "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
            "created_at": "2016-10-15T19:05:50Z",
            "status": "awaiting_applicant",
            "type": "standard",
            "result": "clear",
            "href": "/"
        }
        mock_get.return_value = data
        obj = TestBaseModel(raw={'href': '/'})
        obj.fetch()
        # check that it has update raw, but parsed the return value
        self.assertEqual(obj.raw, data)
        self.assertEqual(obj.onfido_id, data['id'])
        self.assertEqual(obj.created_at, date_parse(data['created_at']))
        # check that it has **not** called the save method
        mock_save.assert_not_called()

        # check what happens if href is missing
        obj = TestBaseModel(raw={})
        self.assertRaises(KeyError, obj.pull)

        # check what happens if API fails
        obj = TestBaseModel(raw={'href': '/'})
        response = mock.Mock()
        response.json.return_value = {
            "error": {
                "fields": {},
                "message": "Authorization error: please re-check your credentials",
                "type": "authorization_error"
            }
        }
        mock_get.side_effect = ApiError(response)
        self.assertRaises(ApiError, obj.pull)

    @mock.patch.object(BaseModel, 'save')
    @mock.patch.object(BaseModel, 'fetch')
    def test_pull(self, mock_fetch, mock_save):
        """Test the pull method calls fetch and save."""
        obj = TestBaseModel(raw={'href': '/'})
        mock_fetch.return_value = obj
        obj.pull()
        # check that it has parsed the return value
        mock_fetch.assert_called_once_with()
        mock_save.assert_called_once_with()


class BaseQuerySetTests(TestCase):

    """onfido.models.BaseQuerySet tests."""

    def create_applicant(self, username):
        """Create new Applicant and user."""
        data = {'id': username, 'created_at': tz_now().isoformat()}
        user = User.objects.create_user(username)
        applicant = Applicant.objects.create_applicant(user, raw=data)
        return applicant

    @mock.patch.object(BaseModel, 'fetch')
    def test_fetch(self, mock_fetch):
        """Test the queryset calls fetch on all objects."""
        # once applicant, one call
        self.create_applicant('fred')
        Applicant.objects.all().fetch()
        mock_fetch.assert_called_once_with()

        # add another applicant, should now call twice
        self.create_applicant('ginger')
        mock_fetch.reset_mock()
        Applicant.objects.all().fetch()
        self.assertEqual(mock_fetch.call_count, 2)

    @mock.patch.object(BaseModel, 'pull')
    def test_pull(self, mock_pull):
        """Test the queryset calls fetch on all objects."""
        # once applicant, one call
        self.create_applicant('fred')
        Applicant.objects.all().pull()
        mock_pull.assert_called_once_with()

        # add another applicant, should now call twice
        self.create_applicant('ginger')
        mock_pull.reset_mock()
        Applicant.objects.all().pull()
        self.assertEqual(mock_pull.call_count, 2)


class BaseStatusModelTests(TestCase):

    """onfido.models.BaseStatusModel tests."""

    def test_defaults(self):
        obj = TestBaseStatusModel()
        self.assertEqual(obj.id, None)
        self.assertEqual(obj.onfido_id, '')
        self.assertEqual(obj.created_at, None)
        self.assertEqual(obj.raw, {})
        self.assertEqual(obj.status, None)
        self.assertEqual(obj.result, None)
        self.assertEqual(obj.updated_at, None)
        self.assertEqual(obj.raw, {})

    def test_parse(self):
        """Test the parse method."""
        data = {
            "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
            "created_at": "2016-10-15T19:05:50Z",
            "status": "awaiting_applicant",
            "type": "standard",
            "result": "clear",
        }
        obj = TestBaseStatusModel().parse(data)
        self.assertEqual(obj.onfido_id, data['id'])
        self.assertEqual(obj.created_at, date_parse(data['created_at']))
        self.assertEqual(obj.status, data['status'])
        self.assertEqual(obj.result, data['result'])

    @mock.patch('onfido.signals.on_status_change.send')
    @mock.patch('onfido.signals.on_completion.send')
    @mock.patch.object(BaseStatusModel, 'pull')
    @mock.patch.object(BaseStatusModel, 'save')
    def test_update_status(self, mock_save, mock_pull, mock_complete, mock_update):
        """Test the update_status method."""
        now = datetime.datetime.now()

        def reset():
            mock_save.reset_mock()
            mock_pull.reset_mock()
            mock_complete.reset_mock()
            mock_update.reset_mock()
            event = Event(
                action='form.opened',
                status='after',
                onfido_id='foo',
                resource_type='check',
                completed_at=now
            )
            obj = TestBaseStatusModel(
                status='before'
            )
            assert obj.status == 'before'
            assert obj.updated_at is None
            return event, obj

        # try passing in something that is not a datetime
        event, obj = reset()
        event.completed_at = None
        self.assertRaises(AssertionError, obj.update_status, event)

        event, obj = reset()
        event.completed_at = now
        obj = obj.update_status(event)
        self.assertEqual(obj.status, event.status)
        self.assertEqual(obj.updated_at, now)
        mock_pull.assert_called_once_with()
        mock_save.assert_not_called()
        mock_update.assert_called_once_with(
            TestBaseStatusModel,
            instance=obj,
            event=event.action,
            status_before='before',
            status_after=event.status
        )
        mock_complete.assert_not_called()

        # if we send 'complete' as the status we should fire the second signal
        event, obj = reset()
        event.status = 'complete'
        obj = obj.update_status(event)
        self.assertEqual(obj.status, event.status)
        self.assertEqual(obj.updated_at, now)
        mock_pull.assert_called_once_with()
        mock_save.assert_not_called()
        mock_update.assert_called_once_with(
            TestBaseStatusModel,
            instance=obj,
            event=event.action,
            status_before='before',
            status_after=event.status
        )
        mock_complete.assert_called_once_with(
            TestBaseStatusModel,
            instance=obj
        )

        # test that we can handle the API failing on pull()
        event, obj = reset()
        mock_pull.side_effect = Exception("Something went wrong in the API")
        obj = obj.update_status(event)
        self.assertEqual(obj.status, event.status)
        self.assertEqual(obj.updated_at, now)
        mock_pull.assert_called_once_with()
        mock_save.assert_called_once_with()
        mock_update.assert_called_once_with(
            TestBaseStatusModel,
            instance=obj,
            event=event.action,
            status_before='before',
            status_after=event.status
        )
        mock_complete.assert_not_called()

    @mock.patch('onfido.models.tz_now')
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
            "href": "http://foo"
        }
        user = User()
        obj = TestBaseStatusModel().parse(data)
        event = obj._override_event(user)
        self.assertEqual(event.onfido_id, obj.onfido_id)
        self.assertEqual(event.action, "manual.override")
        self.assertEqual(event.resource_type, TestBaseStatusModel._meta.model_name)
        self.assertEqual(event.status, obj.status)
        self.assertEqual(event.completed_at, now)

    @mock.patch.object(Event, 'save')
    @mock.patch.object(BaseStatusModel, 'save')
    def test_mark_as_clear(self, mock_save, mock_event_save):
        """Test the mark_as_clear method."""
        data = {
            "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
            "created_at": "2016-10-15T19:05:50Z",
            "status": "awaiting_applicant",
            "type": "standard",
            "result": None,
            "href": "http://foo"
        }
        user = User()
        obj = Check().parse(data)
        self.assertIsNone(obj.is_clear)
        obj = obj.mark_as_clear(user)
        mock_save.assert_called_once_with()
        mock_event_save.assert_called_once_with()
        self.assertTrue(obj.is_clear)

    @mock.patch.object(query.QuerySet, 'filter')
    def test_events(self, mock_filter):
        """Test the events method."""
        obj = TestBaseStatusModel(onfido_id='foo')
        obj.events()
        mock_filter.assert_called_once_with(
            onfido_id='foo',
            resource_type='testbasestatusmodel'
        )


class ApplicantManagerTests(TestCase):

    """onfido.models.ApplicantManager tests."""

    TEST_DATA = {
        "id": "14d2335e-4586-4ac4-aecd-b18296e7d675",
        "created_at": "2016-10-15T19:05:07Z",
    }

    def setUp(self):
        self.user = User(id=1, first_name=u"œ∑´®†¥")
        self.applicant = Applicant(onfido_id='foo', user=self.user)

    @mock.patch.object(BaseModel, 'full_clean')
    def test_create_applicant(self, mock_clean):
        """Test the create method parses response."""
        data = ApplicantManagerTests.TEST_DATA
        applicant = Applicant.objects.create_applicant(user=self.user, raw=data)
        self.assertEqual(applicant.user, self.user)
        self.assertEqual(applicant.raw, data)
        self.assertEqual(applicant.onfido_id, data['id'])
        self.assertEqual(applicant.created_at, date_parse(data['created_at']))


class ApplicantTests(TestCase):

    """onfido.model.Applicant tests."""

    def setUp(self):
        self.user = User(id=1, first_name=u"œ∑´®†¥")
        self.applicant = Applicant(onfido_id='foo', user=self.user)

    def test_defaults(self):
        """Test default property values."""
        applicant = self.applicant
        self.assertEqual(applicant.onfido_id, 'foo')
        self.assertEqual(applicant.user, self.user)
        self.assertEqual(applicant.created_at, None)

    def test_save(self):
        """Test the save method."""
        self.user.save()
        applicant = self.applicant.save()
        self.assertEqual(applicant.onfido_id, 'foo')
        self.assertEqual(applicant.user, self.user)
        self.assertEqual(applicant.created_at, None)
        # test the related_name
        self.assertEqual(self.user.onfido_applicant, applicant)

    def test_unicode_str_repr(self):
        """Test string representations handle unicode."""
        applicant = self.applicant
        self.assertIsNotNone(str(applicant))
        self.assertIsNotNone(unicode(applicant))
        self.assertIsNotNone(repr(applicant))


class CheckManagerTests(TestCase):

    """onfido.models.ApplicantManager tests."""

    @mock.patch.object(BaseModel, 'full_clean')
    def test_create_check(self, mock_clean):
        """Test the create method parses response."""
        user = User.objects.create_user(username='baz', first_name=u"œ∑´®†¥")
        applicant = Applicant(onfido_id='foo', user=user).save()
        data = {
            "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
            "created_at": "2016-10-15T19:05:50Z",
            "status": "awaiting_applicant",
            "type": "standard",
            "result": "clear",
        }
        check = Check.objects.create_check(
            applicant=applicant,
            raw=data
        )
        self.assertEqual(check.user, user)
        self.assertEqual(check.applicant, applicant)
        self.assertEqual(check.onfido_id, data['id'])
        self.assertEqual(check.check_type, data['type'])
        self.assertEqual(check.status, data['status'])
        self.assertEqual(check.result, data['result'])
        self.assertEqual(check.created_at, date_parse(data['created_at']))


class CheckTests(TestCase):

    """onfido.models.Check tests."""

    def setUp(self):
        self.user = User.objects.create_user(username='fred', first_name=u"œ∑´®†¥")
        self.applicant = Applicant(
            onfido_id='foo',
            user=self.user
        ).save()
        self.check = Check(
            onfido_id='bar', user=self.user,
            applicant=self.applicant, check_type='standard'
        ).save()

    def test_defaults(self):
        """Test default property values."""
        check = Check()
        self.assertEqual(check.onfido_id, '')
        self.assertEqual(check.created_at, None)
        self.assertEqual(check.status, None)
        self.assertEqual(check.result, None)
        self.assertEqual(check.check_type, '')

    def test_save(self):
        """Test save method."""
        check = self.check
        self.assertEqual(check.onfido_id, 'bar')
        self.assertEqual(check.created_at, None)
        self.assertEqual(check.status, None)
        self.assertEqual(check.result, None)
        self.assertEqual(check.check_type, 'standard')
        # test the related_names
        self.assertEqual(self.applicant.checks.get(), check)
        self.assertEqual(self.user.onfido_checks.get(), check)

    def test_unicode_str_repr(self):
        """Test string representations handle unicode."""
        check = self.check
        self.assertIsNotNone(str(check))
        self.assertIsNotNone(unicode(check))
        self.assertIsNotNone(repr(check))

    def test_parse(self):
        """Test the parse_raw method."""
        data = {
            "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
            "created_at": "2016-10-15T19:05:50Z",
            "status": "awaiting_applicant",
            "type": "standard",
            "result": "clear",
        }
        check = Check().parse(data)
        # real data taken from check.json
        self.assertEqual(check.onfido_id, "c26f22d5-4903-401f-8a48-7b0211d03c1f")
        self.assertEqual(check.created_at, date_parse(data['created_at']))
        self.assertEqual(check.status, "awaiting_applicant")
        self.assertEqual(check.result, "clear")


class ReportManagerTests(TestCase):

    """onfido.models.ReportManager tests."""

    TEST_DATA = {
        "created_at": "2016-10-18T16:02:08Z",
        "id": "1ffd3e8a-da71-4674-a245-8b52f1492191",
        "name": "identity",
        "result": "clear",
        "status": "awaiting_data",
        "variant": "standard"
    }

    def setUp(self):
        self.user = User.objects.create_user(username="foo", first_name=u"œ∑´®†¥")
        self.applicant = Applicant(
            user=self.user,
            onfido_id='foo',
        ).save()
        self.check = Check(
            user=self.user,
            applicant=self.applicant,
            check_type='standard',
            onfido_id='bar'
        ).save()

    @mock.patch.object(BaseModel, 'full_clean')
    def test_create_report(self, mock_clean):
        """Test the create method parses response."""
        data = ReportManagerTests.TEST_DATA
        report = Report.objects.create_report(
            check=self.check,
            raw=data
        )
        self.assertEqual(report.user, self.user)
        self.assertEqual(report.onfido_check, self.check)
        self.assertEqual(report.onfido_id, data['id'])
        self.assertEqual(report.report_type, data['name'])
        self.assertEqual(report.status, data['status'])
        self.assertEqual(report.result, data['result'])
        self.assertEqual(report.created_at, date_parse(data['created_at']))


class ReportTests(TestCase):

    """onfido.models.Report tests."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="foo",
            first_name=u"œ∑´®†¥"
        )
        self.applicant = Applicant(
            onfido_id='foo',
            user=self.user
        ).save()
        self.check = Check(
            onfido_id='bar',
            user=self.user,
            applicant=self.applicant,
            check_type='standard'
        ).save()
        self.report = Report(
            user=self.user, onfido_id='foo',
            onfido_check=self.check, report_type='identity'
        )

    def test_defaults(self):
        """Test default property values."""
        report = self.report
        self.assertEqual(report.onfido_id, 'foo')
        self.assertEqual(report.created_at, None)
        self.assertEqual(report.status, None)
        self.assertEqual(report.result, None)
        self.assertEqual(report.user, self.user)
        self.assertEqual(report.onfido_check, self.check)
        self.assertEqual(report.report_type, 'identity')

    def test_save(self):
        """Test save method."""
        report = self.report.save()
        self.assertEqual(report.onfido_id, 'foo')
        self.assertEqual(report.created_at, None)
        self.assertEqual(report.status, None)
        self.assertEqual(report.result, None)
        self.assertEqual(report.user, self.user)
        self.assertEqual(report.onfido_check, self.check)
        self.assertEqual(report.report_type, 'identity')
        # test the related_names
        self.assertEqual(self.check.reports.get(), report)
        self.assertEqual(self.user.onfido_reports.get(), report)

    def test_unicode_str_repr(self):
        """Test string representations handle unicode."""
        report = self.report
        self.assertIsNotNone(str(report))
        self.assertIsNotNone(unicode(report))
        self.assertIsNotNone(repr(report))

    def test_parse(self):
        """Test the parse_raw method."""
        data = {
            "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
            "created_at": "2016-10-15T19:05:50Z",
            "status": "awaiting_applicant",
            "result": "clear",
            "name": "identity",
        }
        report = Report().parse(data)
        # real data taken from check.json
        self.assertEqual(report.onfido_id, "c26f22d5-4903-401f-8a48-7b0211d03c1f")
        self.assertEqual(report.created_at, date_parse(data['created_at']))
        self.assertEqual(report.status, "awaiting_applicant")
        self.assertEqual(report.result, "clear")
        self.assertEqual(report.report_type, "identity")

    def test_parse_scrubs_data(self):
        """Test the parse method also removes sensitive data."""
        data = {
            "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
            "created_at": "2016-10-15T19:05:50Z",
            "status": "awaiting_applicant",
            "result": "clear",
            "name": "identity",
            "breakdown": {},
            "properties": {}
        }
        report = Report().parse(data)
        # the default report scrubber should have removed data:
        self.assertFalse('breakdown' in report.raw)
        self.assertFalse('properties' in report.raw)


class EventTests(TestCase):

    """onfido.models.Event tests."""

    TEST_DATA = {
        "payload": {
            "resource_type": "check",
            "action": "check.form_opened",
            "object": {
                "id": "6d7ee353-db1e-4b45-9034-f7e75198cbe0",
                "status": "awaiting_applicant",
                "completed_at": "2016-10-23 12:52:33 UTC",
                "href": "https://api.onfido.com/v1/applicants/xxx"
            }
        }
    }

    def setUp(self):
        self.user = User.objects.create_user(
            username="foo",
            first_name=u"œ∑´®†¥"
        )
        self.applicant = Applicant(
            onfido_id='foo',
            user=self.user
        ).save()
        self.check = Check(
            onfido_id='bar',
            user=self.user,
            applicant=self.applicant,
            check_type='standard'
        ).save()

    def test__resource_manager(self):
        """Test the _resource_manager method."""
        event = Event()
        self.assertRaises(AssertionError, event._resource_manager)
        event.resource_type = 'foo'
        self.assertRaises(AssertionError, event._resource_manager)

        event.resource_type = 'check'
        self.assertEqual(event._resource_manager(), Check.objects)
        event.resource_type = 'report'
        self.assertEqual(event._resource_manager(), Report.objects)

    @mock.patch.object(CheckQuerySet, 'get')
    def test_resource(self, mock_get):
        """Test the resource property."""
        event = Event().parse(EventTests.TEST_DATA)
        event.resource
        mock_get.assert_called_once_with(onfido_id=event.onfido_id)

    @mock.patch.object(CheckQuerySet, 'get')
    def test_user(self, mock_get):
        """Test the resource property."""
        event = Event().parse(EventTests.TEST_DATA)
        event.user
        mock_get.assert_called_once_with(onfido_id=event.onfido_id)

    def test_defaults(self):
        """Test default property values."""
        event = Event()
        # real data taken from check.json
        self.assertEqual(event.resource_type, '')
        self.assertEqual(event.onfido_id, '')
        self.assertEqual(event.action, '')
        self.assertEqual(event.status, '')
        self.assertEqual(event.completed_at, None)
        self.assertEqual(event.raw, {})

    def test_save(self):
        """Test save method."""
        data = EventTests.TEST_DATA
        event = Event().parse(data).save()
        # real data taken from check.json
        self.assertEqual(event.resource_type, data['payload']['resource_type'])
        self.assertEqual(event.onfido_id, data['payload']['object']['id'])
        self.assertEqual(event.action, data['payload']['action'])
        self.assertEqual(event.status, data['payload']['object']['status'])
        self.assertEqual(event.completed_at, date_parse(data['payload']['object']['completed_at']))
        self.assertEqual(event.raw, data)

    def test_unicode_str_repr(self):
        """Test string representations handle unicode."""
        event = Event().parse(EventTests.TEST_DATA)
        self.assertIsNotNone(str(event))
        self.assertIsNotNone(unicode(event))
        self.assertIsNotNone(repr(event))

    def test_parse(self):
        """Test the parse_raw method."""
        data = EventTests.TEST_DATA
        event = Event().parse(data)
        # real data taken from check.json
        self.assertEqual(event.resource_type, data['payload']['resource_type'])
        self.assertEqual(event.onfido_id, data['payload']['object']['id'])
        self.assertEqual(event.action, data['payload']['action'])
        self.assertEqual(event.status, data['payload']['object']['status'])
        self.assertEqual(event.completed_at, date_parse(data['payload']['object']['completed_at']))
        self.assertEqual(event.raw, data)
