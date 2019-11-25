from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import ZENODO_TEST_USER_TOKEN


class TestResourceGETJSON(SimpleTestCase):
    """
    Test the `api_v1/targets/zenodo/resources/{resource_id}.json/` endpoint's GET method.

    Testing Zenodo integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': ZENODO_TEST_USER_TOKEN}
        self.keys = ['kind', 'kind_name', 'id', 'title', 'date_created', 'date_modified', 'hashes',
                     'extra', 'links', 'actions']

    def test_success_resource(self):
        """
        Returns a 200 if the GET method is successful when getting a GitHub `item`.
        """
        # Get a project resource
        resource_id = '3525310'
        extra_keys = ['conceptrecid', 'created', 'doi', 'doi_url', 'files', 'id', 'links', 'metadata',
                      'modified', 'owner', 'record_id', 'state', 'submitted', 'title']

        url = reverse('resource', kwargs={'target_name': 'zenodo',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        self.assertListEqual(extra_keys, list(response.data['extra'].keys()))
        # # Spot check some individual fields
        self.assertEqual('other', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('Test PresQT Project', response.data['title'])
        # # Download, Upload, Transfer Links
        self.assertEqual(len(response.data['links']), 3)

        # Get a file resource
        resource_id = '1644bae0-346b-49af-aaab-2409a688f85e'

        url = reverse('resource', kwargs={'target_name': 'zenodo',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Spot check some individual fields
        self.assertEqual('file', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('1900s_Cat.jpg', response.data['title'])
        # Download Link
        self.assertEqual(len(response.data['links']), 1)

    def test_error_404_not_authorized(self):
        """
        Return a 404 if the GET method fails because the user doesn't have access to this resource
        or it doesn't exist.
        """
        # Try and get a non-existent file
        url = reverse('resource', kwargs={'target_name': 'zenodo',
                                          'resource_id': 'wuy12i-2179840212-21392jds',
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data, {'error': "The resource could not be found by the requesting user."})

        # Try and get a non-existent top level resource
        url = reverse('resource', kwargs={'target_name': 'zenodo',
                                          'resource_id': '1902329',
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data, {'error': "The resource could not be found by the requesting user."})

    def test_error_401_not_authorized_token(self):
        """
        Return a 401 if the GET method fails because the token is invalid.
        """
        url = reverse('resource', kwargs={'target_name': 'zenodo',
                                          'resource_id': '1r66j101q13',
                                          'resource_format': 'json'})
        response = self.client.get(url, **{'HTTP_PRESQT_SOURCE_TOKEN': 'EggmundBoi'})
        # Verify the error status code and message
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.data, {'error': "Zenodo returned a 401 unauthorized status code."})
