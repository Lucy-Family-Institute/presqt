from unittest.mock import patch
from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import CURATE_ND_TEST_TOKEN


class TestResourceGETJSON(TestCase):
    """
    Test the `api_v1/targets/curate_nd/resources/{resource_id}.json/` endpoint's GET method.

    Testing Curate ND integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': CURATE_ND_TEST_TOKEN}
        self.keys = ['kind', 'kind_name', 'id', 'title', 'date_created', 'date_modified', 'hashes',
                     'extra', 'links']

    def test_success_item(self):
        """
        Returns a 200 if the GET method is successful when getting a CurateND `item`.
        """
        resource_id = '1n79h418f06'
        extra_keys = ['creator', 'created', 'creator#administrative_unit', 'rights', 'access',
                      'depositor', 'owner', 'representative', 'hasModel', 'containedFiles']

        url = reverse('resource', kwargs={'target_name': 'curate_nd',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        self.assertListEqual(extra_keys, list(response.data['extra'].keys()))
        # Spot check some individual fields
        self.assertEqual('item', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('Funny Pic', response.data['title'])
        # Since Download/Upload aren't ready `links` should be empty.
        self.assertEqual(len(response.data['links']), 0)

    def test_success_file(self):
        """
        Returns a 200 if the GET method is successful when getting a CurateND `file`.
        """
        resource_id = '1r66j101q13'
        extra_keys = ['mimeType', 'access', 'depositor', 'creator', 'title', 'characterization',
                      'thumbnailUrl', 'hasModel', 'isPartOf']

        url = reverse('resource', kwargs={'target_name': 'curate_nd',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        self.assertListEqual(extra_keys, list(response.data['extra'].keys()))
        # Spot check some individual fields
        self.assertEqual('file', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('DrZ3gwlX0AIbee-.png', response.data['title'])
        # Since Download/Upload aren't ready `links` should be empty.
        self.assertEqual(len(response.data['links']), 0)

    def test_error_403_not_authorized(self):
        """
        Return a 403 if the GET method fails because the user doesn't have access to this resource.
        """
        url = reverse('resource', kwargs={'target_name': 'curate_nd',
                                          'resource_id': 'ns064458c6g',
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data, {'error': "User does not have access to this resource with the token provided."})

    def test_error_404_not_found(self):
        """
        Return a 404 if the GET method fails because the resource doesn't exist.
        """
        url = reverse('resource', kwargs={'target_name': 'curate_nd',
                                          'resource_id': 'eggyboi',
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data, {'error': "Resource not found."})

    def test_error_401_not_authorized_token(self):
        """
        Return a 401 if the GET method fails because the token is invalid.
        """
        url = reverse('resource', kwargs={'target_name': 'curate_nd',
                                          'resource_id': '1r66j101q13',
                                          'resource_format': 'json'})
        response = self.client.get(url, **{'HTTP_PRESQT_SOURCE_TOKEN': 'EggmundBoi'})
        # Verify the error status code and message
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.data, {'error': "Token is invalid. Response returned a 401 status code."})

    def test_error_500_server(self):
        """
        Return a 500 if the GET method fails because of a 500 error on Curate.
        """
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        with patch('requests.Session.get') as fake_get:
            fake_get.return_value = mock_req
            url = reverse('resource', kwargs={'target_name': 'curate_nd',
                                              'resource_id': '1n79h418f06',
                                              'resource_format': 'json'})
            response = self.client.get(url, **self.header)
            # Verify the status code
            self.assertEqual(response.status_code, 500)
            # Verify the response message
            self.assertEqual(response.data, {'error': "CurateND returned a 500 server error."})
