from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from django.test import SimpleTestCase

from config.settings.base import GITLAB_TEST_USER_TOKEN


class TestResourceGETJSON(SimpleTestCase):
    """
    Test the `api_v1/targets/gitlab/resources/{resource_id}.json/` endpoint's GET method.

    Testing GitLab integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_TEST_USER_TOKEN}
        self.keys = ['kind', 'kind_name', 'id', 'title', 'date_created', 'date_modified', 'hashes',
                     'extra', 'links', 'actions']

    def test_success_project(self):
        """
        Returns a 200 if the GET method is successful when getting a GitLab `project`.
        """
        resource_id = '17993268'
        url = reverse('resource', kwargs={'target_name': 'gitlab',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        # Spot check some individual fields
        self.assertEqual('project', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('ProjectNine', response.data['title'])

        self.assertEqual(len(response.data['links']), 3)

    def test_success_dir(self):
        """
        Returns a 200 if the GET method is successful when getting a GitLab `dir`.
        """
        resource_id = '17433066:android'
        url = reverse('resource', kwargs={'target_name': 'gitlab',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        # Spot check some individual fields
        self.assertEqual('dir', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('android', response.data['title'])

        self.assertEqual(len(response.data['links']), 3)

    def test_success_file(self):
        """
        Returns a 200 if the GET method is successful when getting a GitLab `file`.
        """
        resource_id = '17993259:README%2Emd'
        url = reverse('resource', kwargs={'target_name': 'gitlab',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        # Spot check some individual fields
        self.assertEqual('file', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('README.md', response.data['title'])
        # Download Link
        self.assertEqual(len(response.data['links']), 1)

    def test_error_404_not_authorized(self):
        """
        Return a 404 if the GET method fails because the user doesn't have access to this resource
        or it doesn't exist.
        """
        url = reverse('resource', kwargs={'target_name': 'gitlab',
                                          'resource_id': 'supasupabadid',
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
        url = reverse('resource', kwargs={'target_name': 'gitlab',
                                          'resource_id': '17993268',
                                          'resource_format': 'json'})
        response = self.client.get(url, **{'HTTP_PRESQT_SOURCE_TOKEN': 'EggmundBoi'})
        # Verify the error status code and message
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.data, {'error': "Token is invalid. Response returned a 401 status code."})

    def test_error_project(self):
        """
        Returns a 404 if the GET method is unsuccessful when getting a GitLab `project`.
        """
        resource_id = '1743306687'
        url = reverse('resource', kwargs={'target_name': 'gitlab',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'],
                         'The resource could not be found by the requesting user.')

    def test_error_dir(self):
        """
        Returns a 404 if the GET method is unsuccessful when getting a GitLab `dir`.
        """
        resource_id = '17433066:danglesauce'
        url = reverse('resource', kwargs={'target_name': 'gitlab',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'],
                         'The resource could not be found by the requesting user.')

    def test_error_file(self):
        """
        Returns a 404 if the GET method is unsuccessful when getting a GitLab `file`.
        """
        resource_id = '17433066:android%2Fdangles%2Ejson'
        url = reverse('resource', kwargs={'target_name': 'gitlab',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'],
                         'The resource could not be found by the requesting user.')

    def test_bad_project_dir(self):
        """
        Returns a 404 if the GET method is unsuccessful when getting a bad GitLab `project`.
        """
        resource_id = '174330668768:android'
        url = reverse('resource', kwargs={'target_name': 'gitlab',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'],
                         'The resource could not be found by the requesting user.')
