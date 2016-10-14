# -*- coding: utf-8 -*-
import datetime
import json
import mock
import os
import random

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db.models import Model
from django.test import TestCase, TransactionTestCase

from ..models import (
    BaseModel,
    BaseStatusModel,
    Applicant,
    Check,
    Report,
    format_url
)

class TestBaseModel(BaseModel):

    class Meta:
        managed = False

    @property
    def api_get_path(self):
        return '/'


class TestBaseStatusModel(BaseStatusModel):

    class Meta:
        managed = False


class BaseModelTests(TestCase):

    def test_defaults(self):
        obj = TestBaseModel()
        self.assertEqual(obj.id, '')
        self.assertEqual(obj.created_at, None)
        self.assertEqual(obj.raw, {})

    @mock.patch.object(Model, 'save')
    def test_save(self, mock_save):
        """Test that save method returns self."""
        obj = TestBaseModel()
        self.assertEqual(obj.save(), obj)

    def test_api_get_path(self):
        """Test the api_get_path property."""
        obj = BaseModel()
        self.assertRaises(NotImplementedError, lambda: obj.api_get_path)

        obj = TestBaseModel()
        self.assertEqual(obj.api_get_path, '/')

    def test_parse_raw(self):
        """Test the parse_raw method."""
        data = {
          "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
          "created_at": "2016-10-15T19:05:50Z",
          "status": "awaiting_applicant",
          "type": "standard",
          "result": "clear",
        }
        obj = TestBaseModel(raw=data).parse_raw()
        self.assertEqual(obj.id, data['id'])
        self.assertEqual(
            obj.created_at,
            datetime.datetime(2016, 10, 15, 19, 5, 50)
        )

    @mock.patch('onfido.models.get')
    def test_fetch(self, mock_get):
        """Test the fetch method sets the raw field, but does not update."""
        obj = TestBaseModel()
        self.assertEqual(obj.fetch(), obj)
        # assert that we call the API, set the raw
        # field, but do not update the properties
        mock_get.assert_called_once()
        self.assertEqual(obj.raw, mock_get.return_value)

    @mock.patch.object(BaseModel, 'fetch')
    @mock.patch.object(BaseModel, 'parse_raw')
    @mock.patch.object(BaseModel, 'save')
    def test_pull(self, mock_save, mock_parse, mock_fetch):
        """Test the pull method sets and parses the raw field."""
        obj = TestBaseModel()
        # need to ensure that the mock returns obj so that chaining works
        mock_fetch.return_value = obj
        mock_parse.return_value = obj

        obj.pull()
        # assert that we call the API, set the raw
        # field, parse it and save the object
        mock_fetch.assert_called_once()
        mock_parse.assert_called_once()
        mock_save.assert_called_once()


class BaseStatusModelTests(TestCase):

    def test_defaults(self):
        obj = TestBaseStatusModel()
        self.assertEqual(obj.id, '')
        self.assertEqual(obj.created_at, None)
        self.assertEqual(obj.raw, {})
        self.assertEqual(obj.status, 'unknown')
        self.assertEqual(obj.result, 'unknown')
        self.assertEqual(obj.updated_at, None)
        self.assertEqual(obj.raw, {})

    def test_parse_raw(self):
        """Test the parse_raw method."""
        data = {
          "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
          "created_at": "2016-10-15T19:05:50Z",
          "status": "awaiting_applicant",
          "type": "standard",
          "result": "clear",
        }
        obj = TestBaseStatusModel(raw=data).parse_raw()
        self.assertEqual(obj.id, data['id'])
        self.assertEqual(
            obj.created_at,
            datetime.datetime(2016, 10, 15, 19, 5, 50)
        )
        self.assertEqual(obj.status, data['status'])
        self.assertEqual(obj.result, data['result'])

    @mock.patch('onfido.signals.on_status_change.send')
    @mock.patch('onfido.signals.on_completion.send')
    @mock.patch.object(BaseStatusModel, 'save')
    def test_update_status(self, mock_save, mock_complete, mock_update):
        """Test the update_status method."""
        obj = TestBaseStatusModel(status='before')
        now = datetime.datetime.now()
        self.assertEqual(obj.status, 'before')
        self.assertEqual(obj.updated_at, None)

        obj = obj.update_status('report.completed', 'after', now)
        self.assertEqual(obj.status, 'after')
        self.assertEqual(obj.updated_at, now)
        mock_update.assert_called_once_with(
            TestBaseStatusModel,
            instance=obj,
            status_before='before',
            status_after='after'
        )
        mock_complete.assert_not_called()

        # if we send 'complete' as the status we should fire
        # the second signal
        mock_update.reset_mock()
        obj = obj.update_status('report.completed', 'complete', now)
        self.assertEqual(obj.status, 'complete')
        self.assertEqual(obj.updated_at, now)
        mock_update.assert_called_once_with(
            TestBaseStatusModel,
            instance=obj,
            status_before='after',
            status_after='complete'
        )
        mock_complete.assert_called_once_with(
            TestBaseStatusModel,
            instance=obj
        )


class ApplicantManagerTests(TestCase):

    """ApplicantManager tests."""

    def setUp(self):
        self.user = User(id=1, first_name=u"œ∑´®†¥")
        self.applicant = Applicant(id='foo', user=self.user)
        self.data = {
            "id": "14d2335e-4586-4ac4-aecd-b18296e7d675",
            "created_at": "2016-10-15T19:05:07Z",
        }

    @mock.patch('onfido.models.post')
    def test_create_applicant(self, mock_post):
        """Test the create method calls API and parses response."""
        mock_post.return_value = self.data
        applicant = Applicant.objects.create_applicant(user=self.user)
        mock_post.assert_called_once_with(
            format_url(Applicant.POST),
            {
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "email": self.user.email
            }
        )
        self.assertEqual(applicant.raw, self.data)
        self.assertEqual(applicant.id, self.data['id'])
        self.assertEqual(
            applicant.created_at,
            datetime.datetime(2016, 10, 15, 19, 5, 7)
        )

class ApplicantTests(TestCase):

    """Applicant models tests."""

    def setUp(self):
        self.user = User(id=1, first_name=u"œ∑´®†¥")
        self.applicant = Applicant(id='foo', user=self.user)

    def test_defaults(self):
        """Test default property values."""
        applicant = self.applicant
        self.assertEqual(applicant.id, 'foo')
        self.assertEqual(applicant.user, self.user)
        self.assertEqual(applicant.created_at, None)

    def test_unicode_str_repr(self):
        """Test string representations handle unicode."""
        applicant = self.applicant
        self.assertIsNotNone(str(applicant))
        self.assertIsNotNone(unicode(applicant))
        self.assertIsNotNone(repr(applicant))

    def test_api_get_path(self):
        """Test the api_get_path property."""
        applicant = self.applicant
        self.assertEqual(applicant.api_get_path, 'applicants/foo')


class CheckTests(TestCase):

    """Check models tests."""

    def setUp(self):
        self.user = User(id=1, first_name=u"œ∑´®†¥")
        self.applicant = Applicant(id='foo', user=self.user)
        self.check = Check(id='bar', user=self.user, applicant=self.applicant)  # noqa

    def test_defaults(self):
        """Test default property values."""
        check = Check()
        self.assertEqual(check.id, '')
        self.assertEqual(check.created_at, None)
        self.assertEqual(check.status, 'unknown')
        self.assertEqual(check.result, 'unknown')
        self.assertEqual(check.check_type, '')

    def test_unicode_str_repr(self):
        """Test string representations handle unicode."""
        check = self.check
        self.assertIsNotNone(str(check))
        self.assertIsNotNone(unicode(check))
        self.assertIsNotNone(repr(check))

    def test_api_get_path(self):
        """Test the api_get_path property."""
        check = self.check
        self.assertEqual(check.api_get_path, 'applicants/foo/checks/bar')

    def test_parse_raw(self):
        """Test the parse_raw method."""
        data = {
          "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
          "created_at": "2016-10-15T19:05:50Z",
          "status": "awaiting_applicant",
          "type": "standard",
          "result": "clear",
        }
        check = Check(raw=data)
        check.parse_raw()
        # real data taken from check.json
        self.assertEqual(check.id, "c26f22d5-4903-401f-8a48-7b0211d03c1f")
        self.assertEqual(
            check.created_at,
            datetime.datetime(2016, 10, 15, 19, 5, 50)
        )
        self.assertEqual(check.status, "awaiting_applicant")
        self.assertEqual(check.result, "clear")


class ReportTests(TestCase):

    """Report models tests."""

    def setUp(self):
        self.user = User(id=1, first_name=u"œ∑´®†¥")
        self.applicant = Applicant(id='foo', user=self.user)
        self.check = Check(id='bar', user=self.user, applicant=self.applicant)  # noqa
        self.report = Report(id='baz', user=self.user, onfido_check=self.check)  # noqa

    def test_defaults(self):
        """Test default property values."""
        report = self.report
        self.assertEqual(report.id, 'baz')
        self.assertEqual(report.created_at, None)
        self.assertEqual(report.status, 'unknown')
        self.assertEqual(report.result, 'unknown')
        self.assertEqual(report.user, self.user)
        self.assertEqual(report.onfido_check, self.check)
        self.assertEqual(report.report_type, '')

    def test_unicode_str_repr(self):
        """Test string representations handle unicode."""
        report = self.report
        self.assertIsNotNone(str(report))
        self.assertIsNotNone(unicode(report))
        self.assertIsNotNone(repr(report))

    def test_api_get_path(self):
        """Test the api_get_path property."""
        report = self.report
        self.assertEqual(report.api_get_path, 'checks/bar/reports/baz')

    def test_parse_raw(self):
        """Test the parse_raw method."""
        # with open(os.path.join(os.path.dirname(__file__), 'test_files/check.json')) as f:
        #     data = json.load(f)
        data = {
          "id": "c26f22d5-4903-401f-8a48-7b0211d03c1f",
          "created_at": "2016-10-15T19:05:50Z",
          "status": "awaiting_applicant",
          "result": "clear",
          "name": "identity",
        }
        report = Report(raw=data)
        report.parse_raw()
        # real data taken from check.json
        self.assertEqual(report.id, "c26f22d5-4903-401f-8a48-7b0211d03c1f")
        self.assertEqual(
            report.created_at,
            datetime.datetime(2016, 10, 15, 19, 5, 50)
        )
        self.assertEqual(report.status, "awaiting_applicant")
        self.assertEqual(report.result, "clear")
        self.assertEqual(report.report_type, "identity")
