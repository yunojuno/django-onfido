# -*- coding: utf-8 -*-
import mock

from django.test import TestCase

from ..api import (
    get as api_get,
    post as api_post,
    _headers,
    _respond,
    url,
    ONFIDO_API_ROOT,
    ONFIDO_API_KEY,
    ApiError
)

class ApiTests(TestCase):

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
        self.assertEqual(api_get('/'), response.json.return_value)
        mock_get.assert_called_once_with('/', headers=headers)

    @mock.patch('requests.post')
    @mock.patch('onfido.api._headers')
    def test_post(self, mock_headers, mock_post):
        """Test the get function calls API."""
        response = mock.Mock()
        response.status_code = 200
        headers = mock_headers.return_value
        data = {"foo": "bar"}
        mock_post.return_value = response
        self.assertEqual(api_post('/', data), response.json.return_value)
        mock_post.assert_called_once_with('/', headers=headers, json=data)
