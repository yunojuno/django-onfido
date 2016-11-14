# -*- coding: utf-8 -*-
import mock
from copy import deepcopy

from dateutil.parser import parse as date_parse

from django.contrib.auth.models import User
from django.test import TestCase

from ..helpers import (
    create_applicant,
    create_check,
    # import from helpers to deter possible dependency issues
    Applicant,
    Check,
    Report
)


CREATE_APPLICANT_RETURN = {
    "id": "a9acefdf-3dc5-4973-aa78-20bd36825b50",
    "created_at": "2016-10-18T16:02:04Z",
    "title": "Mr",
    "first_name": "Fred",
    "last_name": "Flintstone",
    "email": "fred@flintstone.com",
    "country": "GBR",
}


class HelperTests(TestCase):

    """onfido.helper module tests."""

    @mock.patch('onfido.helpers.post')
    def test_create_applicant(self, mock_post):
        """Test the create_applicant function."""
        data = deepcopy(CREATE_APPLICANT_RETURN)
        mock_post.return_value = data
        user = User.objects.create_user(
            username='fred',
            first_name='Fred',
            last_name='Flintstone',
            email='fred@flintstone.com'
        )
        applicant = create_applicant(user)
        mock_post.assert_called_once_with(
            'applicants',
            {
                'first_name': 'Fred',
                'last_name': 'Flintstone',
                'email': 'fred@flintstone.com',
            }
        )
        self.assertEqual(applicant.onfido_id, data['id'])
        self.assertEqual(applicant.user, user)
        self.assertEqual(applicant.created_at, date_parse(data['created_at']))

    @mock.patch('onfido.helpers.post')
    def test_create_applicant_with_custom_data(self, mock_post):
        """Test the create_applicant function with extra custom POST data."""
        data = deepcopy(CREATE_APPLICANT_RETURN)
        mock_post.return_value = data
        user = User.objects.create_user(
            username='fred',
            first_name='Fred',
            last_name='Flintstone',
            email='fred@flintstone.com'
        )
        create_applicant(
            user,
            country='GBR',
            dob='2016-01-01',
            gender='male'
        )
        mock_post.assert_called_once_with(
            'applicants',
            {
                'first_name': 'Fred',
                'last_name': 'Flintstone',
                'email': 'fred@flintstone.com',
                'gender': 'male',
                'dob': '2016-01-01',
                'country': 'GBR',
            }
        )

    @mock.patch('onfido.helpers.post')
    def test_create_check(self, mock_post):
        """Test the create_check function."""
        applicant_data = deepcopy(CREATE_APPLICANT_RETURN)
        check_data = {
            "id": "b2b75f66-fffd-45a4-ba15-b1e77a672a9a",
            "created_at": "2016-10-18T16:02:08Z",
            "status": "awaiting_applicant",
            "redirect_uri": None,
            "type": "standard",
            "result": None,
            # "form_uri": "https://onfido.com/information/b2b75f66-fffd-45a4-ba15-b1e77a672a9a",
            "reports": [
                {
                    "created_at": "2016-10-18T16:02:08Z",
                    "id": "08345559-852c-4f47-bf65-f9852bf59c4b",
                    "name": "document",
                    "result": None,
                    "status": "awaiting_data",
                    "variant": "standard",
                },
                {
                    "created_at": "2016-10-18T16:02:08Z",
                    "id": "1ffd3e8a-da71-4674-a245-8b52f1492191",
                    "name": "identity",
                    "result": None,
                    "status": "awaiting_data",
                    "variant": "standard",
                }
            ],
        }
        mock_post.return_value = check_data
        user = User.objects.create_user(
            username='fred',
            first_name='Fred',
            last_name='Flintstone',
            email='fred@flintstone.com'
        )
        applicant = Applicant.objects.create_applicant(user, applicant_data)

        # 1. use the defaults.
        check = create_check(applicant, 'standard', ('identity', 'document'))
        mock_post.assert_called_once_with(
            'applicants/a9acefdf-3dc5-4973-aa78-20bd36825b50/checks',
            {'reports': [{'name': 'identity'}, {'name': 'document'}], 'type': 'standard'}
        )
        self.assertEqual(Check.objects.get(), check)
        # check we have two reports, and that the raw field matches the JSON
        # and that the parse method has run
        self.assertEqual(Report.objects.count(), 2)
        for r in check_data['reports']:
            # this will only work if the JSON has been parsed correctly
            report = Report.objects.get(onfido_id=r['id'])
            self.assertEqual(report.raw, r)

        # confirm that asserts guard input
        self.assertRaises(AssertionError, create_check, applicant, 'express', ('identity'))
        self.assertRaises(AssertionError, create_check, applicant, 'standard', 'identity')
        self.assertRaises(AssertionError, create_check, applicant, 'standard', None)

        # confirm that kwargs are merged in correctly
        check.delete()
        mock_post.reset_mock()
        check = create_check(applicant, 'standard', ('identity',), foo='bar')
        mock_post.assert_called_once_with(
            'applicants/a9acefdf-3dc5-4973-aa78-20bd36825b50/checks',
            {'reports': [{'name': 'identity'}], 'type': 'standard', 'foo': 'bar'}
        )
