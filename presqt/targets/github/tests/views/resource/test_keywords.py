import json
import requests
from unittest.mock import patch

from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from django.test import SimpleTestCase

from config.settings.base import GITHUB_TEST_USER_TOKEN


class TestResourceKeywords(SimpleTestCase):
    """
    Test the `api_v1/targets/github/resources/{resource_id}/keywords/` endpoint's GET method.

    Testing GitHub integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}
        self.keys = ['keywords', 'enhanced_keywords']

    def test_success_project_keywords(self):
        """
        Returns a 200 if the GET method is successful when getting a GitHub `repo`.
        """
        resource_id = '209372336'
        url = reverse('keywords', kwargs={'target_name': 'github',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        # Spot check some individual keywords
        self.assertIn('eggs', response.data['keywords'])
        self.assertIn('water', response.data['keywords'])
        self.assertIn('animals', response.data['keywords'])

    def test_error_project_keywords(self):
        """
        Returns a 400 if the GET method is unsuccessful when getting a GitHub `file` keywords.
        """
        resource_id = "209372336:README%252Emd"
        url = reverse('keywords', kwargs={'target_name': 'github',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "GitHub directories and files do not have keywords.")


class TestResourceKeywordsPOST(SimpleTestCase):
    """
    Test the `api_v1/targets/github/resources/{resource_id}/keywords/` endpoint's POST method.

    Testing GitHub integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}
        self.keys = ['keywords_added', 'final_keywords']

    def test_success_project_keywords(self):
        """
        Returns a 202 if the POST method is successful when updating a GitHub `project` keywords.
        """
        resource_id = '209372336'
        url = reverse('keywords', kwargs={'target_name': 'github',
                                          'resource_id': resource_id})
        # First check the initial tags.
        get_response = self.client.get(url, **self.header)
        # Get the ount of the initial keywords
        initial_keywords = len(get_response.data['keywords'])

        response = self.client.post(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 202)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        # Ensure the new list is larger than the initial one.
        self.assertGreater(len(response.data['final_keywords']), initial_keywords)

        # Set the project keywords back to what they were.
        headers = {"Authorization": "token {}".format(GITHUB_TEST_USER_TOKEN),
                   "Accept": "application/vnd.github.mercy-preview+json"}
        put_url = 'https://api.github.com/repos/presqt-test-user/PrivateProject/topics'
        data = {'names': ['eggs', 'water', 'animals']}
        response = requests.put(put_url, headers=headers, data=json.dumps(data))

        self.assertEqual(response.status_code, 200)

    def test_error_project_keywords(self):
        """
        Returns a 400 if the POST method is unsuccessful when getting a GitLab `file` keywords.
        """
        resource_id = "209372336:README%252Emd"
        url = reverse('keywords', kwargs={'target_name': 'github',
                                          'resource_id': resource_id})
        response = self.client.post(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "GitHub directories and files do not have keywords.")

    def test_failed_update_keywords(self):
        # Mock a server error for when a put request is made.
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)
        with patch('requests.put') as mock_request:
            mock_request.return_value = mock_req
            # Upload new keywords
            resource_id = '209372336'
            url = reverse('keywords', kwargs={'target_name': 'github',
                                              'resource_id': resource_id})
            response = self.client.post(url, **self.header)

            # Verify the status code
            self.assertEqual(response.status_code, 400)

            # Ensure the error is what we're expecting.
            self.assertEqual(response.data['error'],
                             "GitHub returned a 500 error trying to update keywords.")
