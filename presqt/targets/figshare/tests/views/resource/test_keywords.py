import json
import requests
from unittest.mock import patch

from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from django.test import SimpleTestCase

from config.settings.base import FIGSHARE_TEST_USER_TOKEN


class TestResourceKeywords(SimpleTestCase):
    """
    Test the `api_v1/targets/figshare/resources/{resource_id}/keywords/` endpoint's GET method.

    Testing FigShare integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': FIGSHARE_TEST_USER_TOKEN}
        self.keys = ['keywords', 'enhanced_keywords', 'all_keywords']

    def test_success_project_keywords(self):
        """
        Returns a 200 if the GET method is successful when getting a FigShare `project`.
        """
        resource_id = '83375:12533801'
        url = reverse('keywords', kwargs={'target_name': 'figshare',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        # Spot check some individual keywords
        self.assertIn('ecoute', response.data['keywords'])
        self.assertIn('listen', response.data['keywords'])
        self.assertIn('ear', response.data['keywords'])

    def test_error_file_keywords(self):
        """
        Returns a 400 if the GET method is unsuccessful when getting a FigShare `file` keywords.
        """
        resource_id = "83375:12533801:23301149"
        url = reverse('keywords', kwargs={'target_name': 'figshare',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "FigShare files do not have keywords.")

    def test_bad_token(self):
        """
        Returns a 401 if token is invalid.
        """
        resource_id = "83375:12533801:23301149"
        url = reverse('keywords', kwargs={'target_name': 'figshare',
                                          'resource_id': resource_id})
        response = self.client.get(url, **{'HTTP_PRESQT_SOURCE_TOKEN': "BAD"})
        # Verify the status code
        self.assertEqual(response.status_code, 401)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "Token is invalid. Response returned a 401 status code.")


class TestResourceKeywordsPOST(SimpleTestCase):
    """
    Test the `api_v1/targets/figshare/resources/{resource_id}/keywords/` endpoint's POST method.

    Testing FigShare integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': FIGSHARE_TEST_USER_TOKEN}
        self.keys = ['initial_keywords', 'keywords_added', 'final_keywords']

    def test_success_article_keywords(self):
        """
        Returns a 202 if the POST method is successful when updating a FigShare `article` keywords.
        """
        resource_id = '83375:12533801'
        url = reverse('keywords', kwargs={'target_name': 'figshare',
                                          'resource_id': resource_id})
        # First check the initial tags.
        get_response = self.client.get(url, **self.header)
        # Get the ount of the initial keywords
        initial_keywords = len(get_response.data['keywords'])

        response = self.client.post(
            url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')
        # Verify the status code
        self.assertEqual(response.status_code, 202)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        # Ensure the new list is larger than the initial one.
        self.assertGreater(len(response.data['final_keywords']), initial_keywords)

        # Set the article keywords back to what they were.
        headers = {"Authorization": "token {}".format(FIGSHARE_TEST_USER_TOKEN)}
        put_url = 'https://api.figshare.com/v2/account/articles/12533801'
        data = {"tags": get_response.data['keywords']}
        response = requests.put(put_url, headers=headers, data=json.dumps(data))

        self.assertEqual(response.status_code, 205)

        # We also need to delete the metadata file.
        project_articles = requests.get("https://api.figshare.com/v2/account/projects/83375/articles",
                                        headers=headers).json()
        for article in project_articles:
            if article['title'] == "PRESQT_FTS_METADATA":
                project_files = requests.get(
                    "{}/files".format(article['url']), headers=headers).json()
                for file in project_files:
                    if file['name'] == "PRESQT_FTS_METADATA.json":
                        response = requests.delete("https://api.figshare.com/v2/account/articles/{}/files/{}".format(
                            article['id'], file['id']),
                            headers=headers)
                        self.assertEqual(response.status_code, 204)
                # Also delete the article
                response = requests.delete(article['url'], headers=headers)
                self.assertEqual(response.status_code, 204)

    def test_error_file_keywords(self):
        """
        Returns a 400 if the POST method is unsuccessful when getting a FigShare `project` keywords.
        """
        resource_id = "7099786765098"
        url = reverse('keywords', kwargs={'target_name': 'figshare',
                                          'resource_id': resource_id})
        response = self.client.post(
            url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "Project with id, 7099786765098, not found for requesting user.")

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
            resource_id = '83375:12533801'
            url = reverse('keywords', kwargs={'target_name': 'figshare',
                                              'resource_id': resource_id})
            response = self.client.post(
                url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')

            # Verify the status code
            self.assertEqual(response.status_code, 400)

            # Ensure the error is what we're expecting.
            self.assertEqual(response.data['error'],
                             "FigShare returned a 500 error trying to update keywords.")
