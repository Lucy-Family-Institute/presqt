import requests
from unittest.mock import patch

from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from django.test import SimpleTestCase

from config.settings.base import GITLAB_TEST_USER_TOKEN


class TestResourceKeywords(SimpleTestCase):
    """
    Test the `api_v1/targets/gitlab/resources/{resource_id}/keywords/` endpoint's GET method.

    Testing GitLab integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_TEST_USER_TOKEN}
        self.keys = ['keywords', 'enhanced_keywords', 'all_keywords']

    def test_success_project_keywords(self):
        """
        Returns a 200 if the GET method is successful when getting a GitLab `project`.
        """
        resource_id = '17993268'
        url = reverse('keywords', kwargs={'target_name': 'gitlab',
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
        resource_id = '17990894'
        # Ensure there are no keywords for this project
        url = reverse('resource', kwargs={'target_name': 'gitlab',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data['extra']['tag_list'], [])

        keywords_url = reverse('keywords', kwargs={'target_name': 'gitlab',
                                                   'resource_id': resource_id})
        keywords_response = self.client.get(keywords_url, **self.header)

        self.assertGreater(keywords_response.data['keywords'], response.data['extra']['tag_list'])

    def test_error_project_keywords(self):
        """
        Returns a 400 if the GET method is unsuccessful when getting a GitLab `file` keywords.
        """
        resource_id = "17993268:README%252Emd"
        url = reverse('keywords', kwargs={'target_name': 'gitlab',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "GitLab directories and files do not have keywords.")


class TestResourceKeywordsPOST(SimpleTestCase):
    """
    Test the `api_v1/targets/gitlab/resources/{resource_id}/keywords/` endpoint's POST method.

    Testing GitLab integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_TEST_USER_TOKEN}
        self.keys = ['initial_keywords', 'keywords_added', 'final_keywords']

    def test_success_project_keywords(self):
        """
        Returns a 202 if the POST method is successful when updating a GitLab `project` keywords.
        """
        resource_id = '17993268'
        url = reverse('keywords', kwargs={'target_name': 'gitlab',
                                          'resource_id': resource_id})
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
        headers = {"Private-Token": "{}".format(GITLAB_TEST_USER_TOKEN)}
        put_url = 'https://gitlab.com/api/v4/projects/{}'.format(resource_id)
        response = requests.put("{}?tag_list=eggs,water,animals".format(put_url), headers=headers)

        self.assertEqual(response.status_code, 200)

        # We also need to delete the metadata file.
        delete_url = "https://gitlab.com/api/v4/projects/{}/repository/files/PRESQT_FTS_METADATA%2Ejson?ref=master".format(
            resource_id)
        data = {
            "branch": "master",
            "commit_message": "PRESQT DELETE METADATA"
        }
        delete_response = requests.delete(delete_url, headers=headers, data=data)
        self.assertEqual(delete_response.status_code, 204)

    def test_error_project_keywords(self):
        """
        Returns a 400 if the POST method is unsuccessful when getting a GitLab `file` keywords.
        """
        resource_id = "17993268:README%252Emd"
        url = reverse('keywords', kwargs={'target_name': 'gitlab',
                                          'resource_id': resource_id})
        response = self.client.post(
            url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "GitLab directories and files do not have keywords.")

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
            resource_id = '17993268'
            url = reverse('keywords', kwargs={'target_name': 'gitlab',
                                              'resource_id': resource_id})
            response = self.client.post(
                url, {"keywords": ["h20", "aqua", "breakfast"]}, **self.header, format='json')

            # Verify the status code
            self.assertEqual(response.status_code, 400)

            # Ensure the error is what we're expecting.
            self.assertEqual(response.data['error'],
                             "GitLab returned a 500 error trying to update keywords.")

    def test_update_project_keywords_through_file_endpoint(self):
        """
        If a file id is provided to the uplaod keywords function, ensure that the projects keywords
        are updated.
        """
        from presqt.targets.gitlab.functions.keywords import gitlab_upload_keywords

        file_id = '17993266:README%2Emd'
        # Check projects existing keywords
        headers = {"Private-Token": GITLAB_TEST_USER_TOKEN}
        get_url = 'https://gitlab.com/api/v4/projects/17993266'

        response = requests.get(get_url, headers=headers).json()
        self.assertEqual(response['tag_list'], [])

        # Make an explicit call to the function
        func_dict = gitlab_upload_keywords(GITLAB_TEST_USER_TOKEN, file_id, ['eggs'])

        # Check the project again and ensure it has a new keyword
        response = requests.get(get_url, headers=headers).json()
        self.assertEqual(response['tag_list'], func_dict['updated_keywords'])

        # Set the poject back to having zero keywords
        put_response = requests.put("{}?tag_list=".format(get_url), headers=headers)

        self.assertEqual(put_response.status_code, 200)
