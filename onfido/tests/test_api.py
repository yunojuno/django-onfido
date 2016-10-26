# -*- coding: utf-8 -*-
import mock

from django.test import TestCase

from ..api import (
    get,
    post,
    _url,
    _headers,
    _respond,
    ApiError,
)


class ApiTests(TestCase):

    """onfido.api module tests."""

    def test__headers(self):
        """Test the _headers function return valid dict."""
        self.assertEqual(
            _headers(api_key="foo"),
            {
                "Authorization": "Token token=foo",
                "Content-Type": "application/json"
            }
        )

    def test__respond(self):
        """Test the _respond function handles 2xx."""
        response = mock.Mock()
        response.status_code = 200
        self.assertEqual(
            _respond(response),
            response.json.return_value
        )
        # non-2xx should raise error
        response.status_code = 400
        response.json.return_value = {
            "error": {
                "message": "foo",
                "type": "bar"
            }
        }
        self.assertRaises(ApiError, _respond, response)

    @mock.patch('requests.get')
    @mock.patch('onfido.api._headers')
    def test_get(self, mock_headers, mock_get):
        """Test the get function calls API."""
        response = mock.Mock()
        response.status_code = 200
        headers = mock_headers.return_value
        mock_get.return_value = response
        self.assertEqual(get('/'), response.json.return_value)
        mock_get.assert_called_once_with(_url('/'), headers=headers)

    @mock.patch('requests.post')
    @mock.patch('onfido.api._headers')
    def test_post(self, mock_headers, mock_post):
        """Test the get function calls API."""
        response = mock.Mock()
        response.status_code = 200
        headers = mock_headers.return_value
        data = {"foo": "bar"}
        mock_post.return_value = response
        self.assertEqual(post('/', data), response.json.return_value)
        mock_post.assert_called_once_with(_url('/'), headers=headers, json=data)
