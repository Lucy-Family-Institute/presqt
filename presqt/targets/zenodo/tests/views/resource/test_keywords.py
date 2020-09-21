import requests
import json
from unittest.mock import patch
from time import sleep

from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from django.test import SimpleTestCase

from config.settings.base import ZENODO_TEST_USER_TOKEN


class TestResourceKeywords(SimpleTestCase):
    """
    Test the `api_v1/targets/zenodo/resources/{resource_id}/keywords/` endpoint's GET method.

    Testing Zenodo integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': ZENODO_TEST_USER_TOKEN}
        self.keys = ['keywords', 'enhanced_keywords', 'all_keywords']

    def test_success_project_keywords(self):
        """
        Returns a 200 if the GET method is successful when getting a Zenodo `project`.
        """
        resource_id = '3525310'
        url = reverse('keywords', kwargs={'target_name': 'zenodo',
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

    def test_success_no_project_keywords_but_metadata_keywords(self):
        """
        If there's no keywords on the target itself we want to check that it's pulling them from
        the metadata file.
        """
        resource_id = '3525982'
        # Ensure no keywords for this project
        url = reverse('resource', kwargs={'target_name': 'zenodo', 'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data['extra']['keywords'], [])

        keywords_url = reverse('keywords', kwargs={'target_name': 'zenodo',
                                                   'resource_id': resource_id})
        keywords_response = self.client.get(keywords_url, **self.header)
        self.assertGreater(keywords_response.data['keywords'], [])

    def test_error_project_keywords(self):
        """
        Returns a 400 if the GET method is unsuccessful when getting a Zenodo `file` keywords.
        """
        resource_id = "1644bae0-346b-49af-aaab-2409a688f85e"
        url = reverse('keywords', kwargs={'target_name': 'zenodo',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "The requested Zenodo resource does not have keywords.")


class TestResourceKeywordsPOST(SimpleTestCase):
    """
    Test the `api_v1/targets/zenodo/resources/{resource_id}/keywords/` endpoint's POST method.

    Testing Zenodo integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': ZENODO_TEST_USER_TOKEN}
        self.keys = ['initial_keywords', 'keywords_added', 'final_keywords']

    def test_success_project_keywords(self):
        """
        Returns a 202 if the POST method is successful when updating a Zenodo `project` keywords.
        """
        resource_id = '3525310'
        url = reverse('keywords', kwargs={'target_name': 'zenodo', 'resource_id': resource_id})
        # First check the initial tags.
        get_response = self.client.get(url, **self.header)
        # Get the count of the initial keywords
        initial_keywords = len(get_response.data['keywords'])

        response = self.client.post(
            url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')
        # Verify the status code
        self.assertEqual(response.status_code, 202)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        # Ensure the new list is larger than the initial one.
        self.assertGreater(len(response.data['final_keywords']), initial_keywords)

        # Set the project keywords back to what they were.
        headers = {"access_token": ZENODO_TEST_USER_TOKEN}
        put_url = 'https://zenodo.org/api/deposit/depositions/{}'.format(resource_id)
        data = {'metadata': {
            "title": "Test PresQT Project",
            "upload_type": "other",
            "description": "<p>This is a test for PresQT.</p>",
            "creators": [{"name": "User, Test"}],
            "keywords": ["eggs", "water", "animals"]}}

        put_response = requests.put(put_url, params=headers, data=json.dumps(data),
                                    headers={'Content-Type': 'application/json'})

        self.assertEqual(put_response.status_code, 200)

        # Delete the created Metadata file.
        # 1. Find the metadata...
        project_info = requests.get(put_url, params=headers).json()
        for file in project_info['files']:
            if file['filename'] == 'PRESQT_FTS_METADATA.json':
                # Get the contents
                response = requests.get(file['links']['download'], params=headers)
                metadata_file = json.loads(response.content)
                # Check keys
                for key, value in metadata_file['actions'][0]['keywords']['ontologies'][0].items():
                    self.assertIn(key, ['keywords', 'ontology', 'ontology_id', 'categories'])
                # 2. Delete the metadata
                delete_url = file['links']['self']
                response = requests.delete(delete_url, params=headers)

                self.assertEqual(response.status_code, 204)

    def test_success_keywords_error_metadata(self):
        """
        Test that if an error occurred during metadata updating, the user is made aware.
        """
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        with patch('requests.post') as mock_request:
            mock_request.return_value = mock_req

            resource_id = '3525310'
            url = reverse('keywords', kwargs={'target_name': 'zenodo',
                                              'resource_id': resource_id})
            # First check the initial tags.
            get_response = self.client.get(url, **self.header)
            # Get the count of the initial keywords
            initial_keywords = len(get_response.data['keywords'])

            response = self.client.post(
                url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')
            # Verify the error
            self.assertEqual(response.status_code, 500)
            # Verify the dict keys match what we expect
            self.assertEqual(
                response.data['error'], 'PresQT Error: Error updating the PresQT metadata file on zenodo. Keywords have been added successfully.')

            updated_response = self.client.get(url, **self.header)
            # Get the ount of the initial keywords
            updated_keywords = len(updated_response.data['keywords'])
            self.assertGreater(updated_keywords, initial_keywords)

        # Set the project keywords back to what they were.
        headers = {"access_token": ZENODO_TEST_USER_TOKEN}
        put_url = 'https://zenodo.org/api/deposit/depositions/{}'.format(resource_id)
        data = {'metadata': {
            "title": "Test PresQT Project",
            "upload_type": "other",
            "description": "<p>This is a test for PresQT.</p>",
            "creators": [{"name": "User, Test"}],
            "keywords": ["eggs", "water", "animals"]}}

        put_response = requests.put(put_url, params=headers, data=json.dumps(data),
                                    headers={'Content-Type': 'application/json'})

        self.assertEqual(put_response.status_code, 200)

    def test_error_project_keywords(self):
        """
        Returns a 400 if the POST method is unsuccessful when getting a Zenodo `file` keywords.
        """
        resource_id = "1644bae0-346b-49af-aaab-2409a688f85e"
        url = reverse('keywords', kwargs={'target_name': 'zenodo',
                                          'resource_id': resource_id})
        response = self.client.post(
            url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "The requested Zenodo resource does not have keywords.")

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
            resource_id = '3525310'
            url = reverse('keywords', kwargs={'target_name': 'zenodo',
                                              'resource_id': resource_id})
            response = self.client.post(
                url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')

            # Verify the status code
            self.assertEqual(response.status_code, 400)

            # Ensure the error is what we're expecting.
            self.assertEqual(response.data['error'],
                             "Zenodo returned a 500 error trying to update keywords.")

    def test_update_project_keywords_if_update_made_on_file(self):
        """
        If a file id is provided, ensure the top level project keywords are updated.
        """
        from presqt.targets.zenodo.functions.keywords import zenodo_upload_keywords

        file_id = 'c67ad447-8afb-42c6-a92c-57936458460e'

        # Check the keywords of this project initially
        headers = {"access_token": ZENODO_TEST_USER_TOKEN}
        get_url = 'https://zenodo.org/api/deposit/depositions/3525982'

        response = requests.get(get_url, params=headers).json()
        if 'keywords' in response['metadata'].keys():
            self.assertEqual(response['metadata']['keywords'], [])

        # Make an explicit call to the function
        func_dict = zenodo_upload_keywords(ZENODO_TEST_USER_TOKEN, file_id, ['eggs'])

        # Check the endpoint again and make sure eggs are there
        updated_response = requests.get(get_url, params=headers).json()
        self.assertEqual(updated_response['metadata']['keywords'], func_dict['updated_keywords'])

        # Delete eggs
        data = {'metadata': {
            "title": response['title'],
            "upload_type": response['metadata']['upload_type'],
            "description": response['metadata']['description'],
            "creators": response['metadata']['creators'],
            "keywords": []
        }}

        put_response = requests.put(get_url, params=headers, data=json.dumps(data),
                                    headers={'Content-Type': 'application/json'})

        self.assertEqual(put_response.status_code, 200)
