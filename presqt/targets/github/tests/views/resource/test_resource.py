import os
import shutil
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import GITHUB_TEST_USER_TOKEN


class TestResourceGETJSON(SimpleTestCase):
    """
    Test the `api_v1/targets/github/resources/{resource_id}.json/` endpoint's GET method.

    Testing GitHub integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}
        self.keys = ['kind', 'kind_name', 'id', 'title', 'date_created', 'date_modified', 'hashes',
                     'extra', 'links', 'actions']

    def test_success_repo(self):
        """
        Returns a 200 if the GET method is successful when getting a GitHub `item`.
        """
        resource_id = '209372092'
        extra_keys = ['id', 'node_id', 'name', 'full_name', 'private', 'owner',
                      'description', 'fork', 'url', 'created_at', 'updated_at', 'pushed_at',
                      'homepage', 'size', 'stargazers_count', 'watchers_count', 'language',
                      'has_issues', 'has_projects', 'has_downloads', 'has_wiki', 'has_pages',
                      'forks_count', 'archived', 'disabled', 'open_issues_count', 'license',
                      'forks', 'open_issues', 'watchers', 'default_branch', 'permissions',
                      'temp_clone_token', 'allow_squash_merge', 'allow_merge_commit',
                      'allow_rebase_merge', 'network_count', 'subscribers_count']

        url = reverse('resource', kwargs={'target_name': 'github',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        self.assertListEqual(extra_keys, list(response.data['extra'].keys()))
        # Spot check some individual fields
        self.assertEqual('repo', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('ProjectTwo', response.data['title'])
        # Download Link
        self.assertEqual(len(response.data['links']), 1)

    def test_error_404_not_authorized(self):
        """
        Return a 404 if the GET method fails because the user doesn't have access to this resource
        or it doesn't exist.
        """
        url = reverse('resource', kwargs={'target_name': 'github',
                                          'resource_id': '18749720',
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
        url = reverse('resource', kwargs={'target_name': 'github',
                                          'resource_id': '1r66j101q13',
                                          'resource_format': 'json'})
        response = self.client.get(url, **{'HTTP_PRESQT_SOURCE_TOKEN': 'EggmundBoi'})
        # Verify the error status code and message
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.data, {'error': "The response returned a 401 unauthorized status code."})
