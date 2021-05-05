from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, HttpResponseForbidden
from django.test import RequestFactory, TestCase

from onfido.decorators import _hmac, _match, verify_signature

# taken from a real requestbin webhook callback
TEST_WEBHOOK_TOKEN = b"ileDMrEn29YPQqZBZi8HJ-e33nqXMrtx"
TEST_REQUEST_SIGNATURE = (
    "bac836ffcc32856bcf70deb77dd63e432ab13e4d940751db927795f616c85352"
)
# HttpRequest.body is a bytestring
TEST_REQUEST_BODY = (
    b'{"payload":{"resource_type":"check","action":"check.started",'
    b'"object":{"id":"08f64599-e484-4870-8227-b4a52861a656",'
    b'"status":"in_progress","completed_at_iso8601":"2021-02-19T16:30:03Z",'
    b'"href":"https://api.onfido.com/v3/checks/08f64599-e484-4870-8227-b4a52861a656"}}}'
)


class DecoratorTests(TestCase):

    """onfido.decorator module tests."""

    def setUp(self):
        self.factory = RequestFactory()

    def get_request(self, body=TEST_REQUEST_BODY, signature=TEST_REQUEST_SIGNATURE):
        """Create test request."""
        if signature:
            return self.factory.post(
                "/",
                body,
                content_type="application/json",
                HTTP_X_SHA2_SIGNATURE=signature,
            )
        else:
            return self.factory.post("/", body, content_type="application/json")

    def test__hmac(self):
        """Test the _hmac function."""
        self.assertEqual(
            _hmac(TEST_WEBHOOK_TOKEN, TEST_REQUEST_BODY), TEST_REQUEST_SIGNATURE
        )

    def test__match(self):
        """Test the _match function."""

        def match(token, body):
            request = self.get_request(body)
            return _match(token, request)

        self.assertTrue(match(TEST_WEBHOOK_TOKEN, TEST_REQUEST_BODY))
        self.assertFalse(match("foo", TEST_REQUEST_BODY))
        self.assertFalse(match(TEST_WEBHOOK_TOKEN, "bar"))

        # test with a good request, but various HMAC error
        with mock.patch("onfido.decorators._hmac") as mock_hmac:
            mock_hmac.side_effect = KeyError()
            self.assertFalse(match(TEST_WEBHOOK_TOKEN, TEST_REQUEST_BODY))
            mock_hmac.side_effect = Exception("We are f-secure")
            self.assertFalse(match(TEST_WEBHOOK_TOKEN, TEST_REQUEST_BODY))

        # test bad request (missing the X-Signature header)
        request = self.get_request(signature=None)
        self.assertFalse(_match(TEST_WEBHOOK_TOKEN, request))

    @mock.patch("onfido.decorators._match")
    def test_verify_signature(self, mock_match):
        """Test the view function decorator itself."""

        @verify_signature()
        def request_function(request):
            """Fake view function that just returns a 200."""
            return HttpResponse()

        request = self.get_request()

        # import module as we want to manipulate the WEBHOOK_TOKEN
        from onfido import decorators

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
