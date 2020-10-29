import json
import requests
from unittest.mock import patch

from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from django.test import SimpleTestCase

from config.settings.base import OSF_TEST_USER_TOKEN
from presqt.utilities import PresQTResponseException


class TestResourceKeywords(SimpleTestCase):
    """
    Test the `api_v1/targets/osf/resources/{resource_id}/keywords/` endpoint's GET method.

    Testing OSF integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN}
        self.keys = ['keywords', 'enhanced_keywords', 'all_keywords']

    def test_success_project_keywords(self):
        """
        Returns a 200 if the GET method is successful when getting an OSF `project`.
        """
        resource_id = 'cmn5z'
        url = reverse('keywords', kwargs={'target_name': 'osf',
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

    def test_success_file_keywords(self):
        """
        Returns a 200 if the GET method is successful when getting an OSF `file`.
        """
        resource_id = '5cd9831c054f5b001a5ca2af'
        url = reverse('keywords', kwargs={'target_name': 'osf',
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
        self.assertIn('PresQT', response.data['keywords'])

    def test_success_folder_keywords(self):
        """
        Returns a 200 if there are no keywords for the folder, but we find keywords in the metadata file.
        """
        resource_id = '5cd98b0af244ec0021e5f8dd'
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # # Verify the status code
        self.assertEqual(response.status_code, 200)
       # Spot check some individual keywords
        self.assertIn('eggs', response.data['keywords'])
        self.assertIn('water', response.data['keywords'])
        self.assertIn('animals', response.data['keywords'])
        self.assertIn('presqt', response.data['keywords'])

    def test_error_storage_keywords(self):
        """
        Returns a 400 if the GET method is unsuccessful when getting an OSF `storage` keywords.
        """
        resource_id = "cmn5z:googledrive"
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "On OSF only projects, folders and files have keywords, not storages, therefore PresQT keyword features are not supported at OSF's storage level.")

    def test_invalid_token(self):
        """
        Returns a 401 if token is bad.
        """
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': 'EGGS'}
        resource_id = "cmn5z:googledrive"
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 401)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "Token is invalid. Response returned a 401 status code.")

    def test_no_token(self):
        resource_id = '5cd98b0af244ec0021e5f8dd'
        self.header = {}
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(
            response.data['error'], "PresQT Error: 'presqt-source-token' missing in the request headers.")


class TestResourceKeywordsPOST(SimpleTestCase):
    """
    Test the `api_v1/targets/osf/resources/{resource_id}/keywords/` endpoint's POST method.

    Testing OSF integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN}
        self.keys = ['initial_keywords', 'keywords_added', 'final_keywords']

    def test_invalid_token(self):
        """
        Returns a 401 if token is bad.
        """
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': 'EGGS'}
        resource_id = "cmn5z"
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.post(
            url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')
        # Verify the status code
        self.assertEqual(response.status_code, 401)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "Token is invalid. Response returned a 401 status code.")

    def test_success_project_keywords(self):
        """
        Returns a 202 if the POST method is successful when updating a OSF `project` keywords.
        """
        resource_id = 'cmn5z'
        url = reverse('keywords', kwargs={'target_name': 'osf', 'resource_id': resource_id})
        # First check the initial keywords.
        get_response = self.client.get(url, **self.header)
        # Get the count of the initial keywords
        initial_keywords = len(get_response.data['keywords'])

        # Get the contents of  the FTS_METADATA file
        metadata_url = 'https://api.osf.io/v2/files/5f68f4d846080900ba1aed07/'
        metadata_headers = {'Authorization': 'Bearer {}'.format(OSF_TEST_USER_TOKEN)}
        metadata_json = requests.get(metadata_url, headers=metadata_headers).json()
        metadata_contents = requests.get(
            metadata_json['data']['links']['move'], headers=metadata_headers).content

        response = self.client.post(
            url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')
        # Verify the status code
        self.assertEqual(response.status_code, 202)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        self.assertGreater(len(response.data['final_keywords']), initial_keywords)

        # Set the project keywords back to what they were.
        headers = {'Authorization': 'Bearer {}'.format(OSF_TEST_USER_TOKEN),
                   'Content-Type': 'application/json'}
        patch_url = 'https://api.osf.io/v2/nodes/{}/'.format(resource_id)
        data = {"data": {"type": "nodes", "id": resource_id, "attributes": {
            "tags": ['eggs', 'water', 'animals']}}}

        response = requests.patch(patch_url, headers=headers, data=json.dumps(data))
        self.assertEqual(response.status_code, 200)

        post_metadata_json = requests.get(metadata_url, headers=metadata_headers).json()
        post_metadata_contents = json.loads(requests.get(
            post_metadata_json['data']['links']['move'], headers=metadata_headers).content)

        # Check that the metadata keyword keys are there
        for key, value in post_metadata_contents['actions'][0]['keywords']['ontologies'][0].items():
            self.assertIn(key, ['keywords', 'ontology', 'ontology_id', 'categories'])

        # Set the metadata back to what it was.
        metadata_response = requests.put(metadata_json['data']['links']['upload'], headers=metadata_headers, params={
                                         'kind': 'file'}, data=metadata_contents)
        self.assertEqual(metadata_response.status_code, 200)

    def test_success_file_keywords(self):
        """
        Returns a 202 if the POST method is successful when updating a OSF `file` keywords.
        """
        resource_id = '5cd9831c054f5b001a5ca2af'
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        # First check the initial tags.
        get_response = self.client.get(url, **self.header)

        # Get the count of the initial keywords
        initial_keywords = len(get_response.data['keywords'])

        # Get the contents of  the FTS_METADATA file
        metadata_url = 'https://api.osf.io/v2/files/5f68f4d846080900ba1aed07/'
        metadata_headers = {'Authorization': 'Bearer {}'.format(OSF_TEST_USER_TOKEN)}
        metadata_json = requests.get(metadata_url, headers=metadata_headers).json()
        metadata_contents = requests.get(
            metadata_json['data']['links']['move'], headers=metadata_headers).content

        response = self.client.post(
            url, {"keywords": ["h20", "aqua", "breakfast", "spaghetti", "wood"]}, **self.header, format='json')
        # Verify the status code
        self.assertEqual(response.status_code, 202)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        # Ensure the new list is equal to the initial one
        self.assertGreater(len(response.data['final_keywords']), initial_keywords)

        # Set the project keywords back to what they were.
        headers = {'Authorization': 'Bearer {}'.format(OSF_TEST_USER_TOKEN),
                   'Content-Type': 'application/json'}
        patch_url = 'https://api.osf.io/v2/files/{}/'.format(resource_id)
        data = {"data": {"type": "files", "id": resource_id, "attributes": {
            "tags": ['eggs', 'water', 'animals', 'PresQT']}}}

        response = requests.patch(patch_url, headers=headers, data=json.dumps(data))
        self.assertEqual(response.status_code, 200)

        # Set the metadata back to what it was.
        metadata_response = requests.put(metadata_json['data']['links']['upload'], headers=metadata_headers, params={
                                         'kind': 'file'}, data=metadata_contents)
        self.assertEqual(metadata_response.status_code, 200)

    def test_error_storage_keywords(self):
        """
        Returns a 400 if the POST method is unsuccessful when getting a OSF `storage` keywords.
        """
        resource_id = 'cmn5z:googledrive'
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.post(
            url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "On OSF only projects, folders and files have keywords, not storages, therefore PresQT keyword features are not supported at OSF's storage level.")

    def test_error_no_keywords(self):
        """
        Returns a 400 if the POST method is unsuccessful when getting a OSF `folder` keywords.
        """
        resource_id = '5cd98b0af244ec0021e5f8dd'
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.post(
            url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         'OSF returned a 404 error trying to update keywords.')

    def test_error_no_keywords_provided(self):
        """
        Returns a 400 if the POST method is unsuccessful when no keywords provided.
        """
        resource_id = '5cd98b0af244ec0021e5f8dd'
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.post(
            url, {"eggs": ["h20", "aqua", "breakfast"]}, **self.header, format='json')
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "PresQT Error: 'keywords' is missing from the request body.")

    def test_no_token(self):
        resource_id = '5cd98b0af244ec0021e5f8dd'
        self.header = {}
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.post(
            url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(
            response.data['error'], "PresQT Error: 'presqt-source-token' missing in the request headers.")

    def test_error_keywords_not_list(self):
        """
        Returns a 400 if the POST method is unsuccessful when keywords is not in list format.
        """
        resource_id = '5cd98b0af244ec0021e5f8dd'
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.post(url, {"keywords": "h20"}, **self.header, format='json')
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'], "PresQT Error: 'keywords' must be in list format.")

    def test_failed_update_keywords_project(self):
        # Mock a server error for when a put request is made.
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)
        with patch('requests.patch') as mock_request:
            mock_request.return_value = mock_req
            # Upload new keywords
            resource_id = 'cmn5z'
            url = reverse('keywords', kwargs={'target_name': 'osf',
                                              'resource_id': resource_id})
            response = self.client.post(
                url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')

            # Verify the status code
            self.assertEqual(response.status_code, 400)

            # Ensure the error is what we're expecting.
            self.assertEqual(response.data['error'],
                             "OSF returned a 500 error trying to update keywords.")

    def test_failed_update_keywords_files(self):
        # Mock a server error for when a put request is made.
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)
        with patch('requests.patch') as mock_request:
            mock_request.return_value = mock_req
            # Upload new keywords
            resource_id = '5cd9831c054f5b001a5ca2af'
            url = reverse('keywords', kwargs={'target_name': 'osf',
                                              'resource_id': resource_id})
            response = self.client.post(
                url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')

            # Verify the status code
            self.assertEqual(response.status_code, 400)

            # Ensure the error is what we're expecting.
            self.assertEqual(response.data['error'],
                             "OSF returned a 500 error trying to update keywords.")

    def test_bad_token_on_upload_function(self):
        """
        If the token provided is invalid, raise an error.
        """
        from presqt.targets.osf.functions.keywords import osf_upload_keywords
        self.assertRaises(PresQTResponseException, osf_upload_keywords,
                          'badtoken', 'badid', ['eggs'])
