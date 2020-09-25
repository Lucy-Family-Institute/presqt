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
        self.keys = ['keywords', 'enhanced_keywords', 'all_keywords']

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

    def test_success_no_project_keywords_but_metadata_keywords(self):
        """
        If there's no keywords on the target itself we want to check that it's pulling them from
        the metadata file.
        """
        resource_id = '209373761'
        # Ensure no keywords for this project
        url = reverse('resource', kwargs={'target_name': 'github',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data['extra']['topics'], [])

        keywords_url = reverse('keywords', kwargs={'target_name': 'github',
                                                   'resource_id': resource_id})
        keywords_response = self.client.get(keywords_url, **self.header)
    
        self.assertGreater(keywords_response.data['keywords'], response.data['extra']['topics'])

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
                         "Only Github repositories have keywords, not files or directories, therefore PresQT keyword features are not supported at Github's file or directory level.")


class TestResourceKeywordsPOST(SimpleTestCase):
    """
    Test the `api_v1/targets/github/resources/{resource_id}/keywords/` endpoint's POST method.

    Testing GitHub integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}
        self.keys = ['initial_keywords', 'keywords_added', 'final_keywords']

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

        response = self.client.post(
            url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')
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

        # Delete the metadata file
        # First get the sha, which will ensure the metadata file exists....
        file_url = 'https://api.github.com/repos/presqt-test-user/PrivateProject/contents/PRESQT_FTS_METADATA.json'
        file = requests.get(file_url, headers=headers).json()
        file_sha = file['sha']
        file_contents_raw = requests.get("https://raw.githubusercontent.com/presqt-test-user/PrivateProject/master/PRESQT_FTS_METADATA.json", headers=headers).content
        file_contents = json.loads(file_contents_raw)

        # Check keys in keywords
        for key, value in file_contents['actions'][0]['keywords']['ontologies'][0].items():
            self.assertIn(key, ['keywords', 'ontology', 'ontology_id', 'categories'])

        data = {
            "message": "Delete Metadata",
            "committer": {
                "name": "PresQT",
                "email": "N/A"
            },
            "sha": file_sha
        }

        delete_response = requests.delete(file_url, headers=headers, data=json.dumps(data))
        self.assertEqual(delete_response.status_code, 200)

    def test_error_project_keywords(self):
        """
        Returns a 400 if the POST method is unsuccessful when getting a GitHub `file` keywords.
        """
        resource_id = "209372336:README%252Emd"
        url = reverse('keywords', kwargs={'target_name': 'github',
                                          'resource_id': resource_id})
        response = self.client.post(
            url, data={"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "Only Github repositories have keywords, not files or directories, therefore PresQT keyword features are not supported at Github's file or directory level.")

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
            response = self.client.post(
                url, data={"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')

            # Verify the status code
            self.assertEqual(response.status_code, 400)

            # Ensure the error is what we're expecting.
            self.assertEqual(response.data['error'],
                             "GitHub returned a 500 error trying to update keywords.")

    def test_update_project_keywords_through_file_endpoint(self):
        """
        If a file id is provided to the uplaod keywords function, ensure that the projects keywords
        are updated.
        """
        from presqt.targets.github.functions.keywords import github_upload_keywords

        file_id = '209373421:README%252Emd'
        # Check projects existing keywords
        headers = {"Authorization": "token {}".format(GITHUB_TEST_USER_TOKEN),
                   "Accept": "application/vnd.github.mercy-preview+json"}
        get_url = 'https://api.github.com/repositories/209373421/topics'

        response = requests.get(get_url, headers=headers).json()
        self.assertEqual(response['names'], [])

        # Make an explicit call to the function
        func_dict = github_upload_keywords(GITHUB_TEST_USER_TOKEN, file_id, ['eggs'])

        # Check the project again and ensure it has a new keyword
        response = requests.get(get_url, headers=headers).json()
        self.assertEqual(response['names'], func_dict['updated_keywords'])

        # Set the poject back to having zero keywords
        data = {'names': []}
        put_response = requests.put(get_url, headers=headers, data=json.dumps(data))

        self.assertEqual(put_response.status_code, 200)

    def test_update_project_keywords_more_than_20_keywords(self):
        """
        If more than 20 keywords are included in the keyword list, ensure only 20 post to GitHub.
        """
        from presqt.targets.github.functions.keywords import github_upload_keywords

        file_id = '209373421'
        # Check projects existing keywords
        headers = {"Authorization": "token {}".format(GITHUB_TEST_USER_TOKEN),
                   "Accept": "application/vnd.github.mercy-preview+json"}
        get_url = 'https://api.github.com/repositories/209373421/topics'

        response = requests.get(get_url, headers=headers).json()
        self.assertEqual(response['names'], [])

        # Make an explicit call to the function
        long_boi_list = ['overt', 'yoke', 'acoustics', 'rare', 'stupid', 'geese', 'spray', 'knit',
                         'shaggy', 'weigh', 'sable', 'interfere', 'swing', 'accurate', 'overjoyed', 'point',
                         'stretch', 'abrasive', 'fog', 'brash', 'delight', 'succeed']
        func_dict = github_upload_keywords(GITHUB_TEST_USER_TOKEN, file_id, long_boi_list)

        # Check the project again and ensure it has the new keywords, and length is only 20
        response = requests.get(get_url, headers=headers).json()
        self.assertEqual(response['names'], func_dict['updated_keywords'])
        self.assertEqual(len(response['names']), 20)

        # Set the poject back to having zero keywords
        data = {'names': []}
        put_response = requests.put(get_url, headers=headers, data=json.dumps(data))

        self.assertEqual(put_response.status_code, 200)
