# -*- coding: utf-8 -*-
import mock

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, HttpResponseForbidden
from django.test import (
    TestCase,
    RequestFactory,
    override_settings
)
from ..decorators import (
    _hmac,
    _match,
    verify_signature
)

# taken from a real requestbin webhook callback
TEST_WEBHOOK_TOKEN = 'bLFiN4S09FV1nH5G7ZJc3nCYqeMZrHcU'
TEST_REQUEST_SIGNATURE = '32f77520f7b025f15ef3ab55be178667c92827e3'
TEST_REQUEST_BODY = (
    '{"payload":{"resource_type":"check","action":"check.form_opened",'
    '"object":{"id":"923d2717-9abd-4c0b-bc4f-33d769547df5",'
    '"status":"awaiting_applicant","completed_at":"2016-10-26 16:18:24 UTC",'
    '"href":"https://api.onfido.com/v1/applicants/4d2ff0dc-3352-4eed-9b7c-'
    '86ac7b619e4e/checks/923d2717-9abd-4c0b-bc4f-33d769547df5"}}}'
)


class DecoratorTests(TestCase):

    """onfido.decorator module tests."""

    def setUp(self):
        self.factory = RequestFactory()

    def get_request(self, body=TEST_REQUEST_BODY, signature=TEST_REQUEST_SIGNATURE):
        """Create test request."""
        if signature:
            return self.factory.post(
                '/', body,
                content_type='application/json',
                HTTP_X_SIGNATURE=signature
            )
        else:
            return self.factory.post(
                '/', body,
                content_type='application/json'
            )

    def test__hmac(self):
        """Test the _hmac function."""
        self.assertEqual(
            _hmac(TEST_WEBHOOK_TOKEN, TEST_REQUEST_BODY),
            TEST_REQUEST_SIGNATURE
        )

    def test__match(self):
        """Test the _match function."""

        def match(token, body):
            request = self.get_request(body)
            return _match(token, request)

        self.assertTrue(match(TEST_WEBHOOK_TOKEN, TEST_REQUEST_BODY))
        self.assertFalse(match('foo', TEST_REQUEST_BODY))
        self.assertFalse(match(TEST_WEBHOOK_TOKEN, 'bar'))

        # test with a good request, but various HMAC error
        with mock.patch('onfido.decorators._hmac') as mock_hmac:
            mock_hmac.side_effect = KeyError()
            self.assertFalse(match(TEST_WEBHOOK_TOKEN, TEST_REQUEST_BODY))
            mock_hmac.side_effect = Exception("We are f-secure")
            self.assertFalse(match(TEST_WEBHOOK_TOKEN, TEST_REQUEST_BODY))

        # test bad request (missing the X-Signature header)
        request = self.get_request(signature=None)
        self.assertFalse(_match(TEST_WEBHOOK_TOKEN, request))

    @mock.patch('onfido.decorators._match')
    def test_verify_signature(self, mock_match):
        """Test the view function decorator itself."""

        @verify_signature()
        def request_function(request):
            """Fake view function that just returns a 200."""
            return HttpResponse()

        request = self.get_request()

        # import module as we want to manipulate the WEBHOOK_TOKEN
        from .. import decorators

        # in TEST_MODE we return immediately
        decorators.TEST_MODE = True
        decorators.WEBHOOK_TOKEN = None
        mock_match.reset_mock()
        request_function(request)
        mock_match.assert_not_called()

        # without a WEBHOOK_TOKEN we should get an error
        decorators.TEST_MODE = False
        decorators.WEBHOOK_TOKEN = None
        self.assertRaises(ImproperlyConfigured, request_function, request)
        mock_match.assert_not_called()

        # mock out _hmac so we can force a pass / fail
        decorators.TEST_MODE = False
        decorators.WEBHOOK_TOKEN = TEST_WEBHOOK_TOKEN
        mock_match.return_value = True
        self.assertIsInstance(request_function(request), HttpResponse)
        mock_match.return_value = False
        self.assertIsInstance(request_function(request), HttpResponseForbidden)
