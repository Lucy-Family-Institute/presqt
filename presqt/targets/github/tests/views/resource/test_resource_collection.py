import os
import shutil
import time
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import GITHUB_TEST_USER_TOKEN
from presqt.targets.github.utilities import delete_github_repo
from presqt.targets.utilities import shared_upload_function_github

class TestResourceCollection(SimpleTestCase):
    """
    Test the 'api_v1/targets/github/resources' endpoint's GET method.

    Testing GitHub integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}

    def test_success_github(self):
        """
        Return a 200 if the GET method is successful when grabbing GitHub resources.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect,
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))
        # Verify the count of resource objects is what we expect.
        self.assertEqual(len(response.data), 31)

        for data in response.data:
            self.assertEqual(len(data['links']), 1)

    def test_error_400_missing_token_github(self):
        """
        Return a 400 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        response = self.client.get(url)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "'presqt-source-token' missing in the request headers."})

    def test_error_401_invalid_token_github(self):
        """
        Return a 401 if the token provided is not a valid token.
        """
        client = APIClient()
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'eggyboi'}
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        response = client.get(url, **header)
        # Verify the error status code and message.
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "The response returned a 401 unauthorized status code."})


class TestResourceCollectionPOST(SimpleTestCase):
    """
    Test the endpoint's POST method for resource uploads:
         `api_v1/targets/{target_name}/resources/{resource_id}/`
         `api_v1/targets/{target_name}/resources/`

    Testing GitHub integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.token = GITHUB_TEST_USER_TOKEN
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': self.token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        self.repo_title = 'NewProject'

        self.resource_id = None
        self.duplicate_action = 'ignore'
        self.url = reverse('resource_collection', kwargs={'target_name': 'github'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.resources_ignored = []
        self.resources_updated = []
        self.hash_algorithm = 'md5'

    def tearDown(self):
        """
        This should run at the end of this test class
        """
        delete_github_repo('presqt-test-user', self.repo_title,
                           {'Authorization': 'token {}'.format(GITHUB_TEST_USER_TOKEN)})

    def test_success_202_upload(self):
        """
        Return a 202 when a file is uploading.
        """
        # 202 when uploading a new top level repo
        shared_upload_function_github(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}).json()

        repo_name_list = [repo['title'] for repo in response_json]
        self.assertIn(self.repo_title, repo_name_list)
        # Delete upload folder
        shutil.rmtree(self.ticket_path)

    def test_success_202_empty_folder(self):
        """
        If an empty directory is included in the uploaded project, we want to ensure the user is
        made aware.
        """
        bag_with_empty_directory = 'presqt/api_v1/tests/resources/upload/Empty_Directory_Bag.zip'
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(self.url, {'presqt-file': open(bag_with_empty_directory, 'rb')},
                                    **self.headers)

        ticket_number = response.data['ticket_number']
        self.ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        time.sleep(5)

        upload_job_response = self.client.get(response.data['upload_job'], **self.headers)

        # Verify status code and message
        self.assertEqual(upload_job_response.data['resources_ignored'], ['/Egg/Empty_Folder'])

        delete_github_repo('presqt-test-user', 'Egg',
                           {'Authorization': 'token {}'.format(GITHUB_TEST_USER_TOKEN)})
        # Delete upload folder
        shutil.rmtree(self.ticket_path)

    def test_handle_repo_duplication(self):
        """
        If a repo with this name already exists for the user, PresQT should handle repo duplication.
        """
        # What the new repo should be named
        duplicate_title = "{}-PresQT1-".format(self.repo_title)
        second_duplicate_title = "{}-PresQT2-".format(self.repo_title)
        # 202 when uploading a new top level repo
        shared_upload_function_github(self)

        shutil.rmtree(self.ticket_path)

        # Verify the duplicate repo does not exist on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}).json()

        repo_name_list = [repo['title'] for repo in response_json]
        self.assertNotIn(duplicate_title, repo_name_list)

        # Make the second post attempt
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        time.sleep(10)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        updated_response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}).json()

        updated_repo_name_list = [repo['title'] for repo in updated_response_json]
        self.assertIn(duplicate_title, updated_repo_name_list)

        # Delete upload folder
        shutil.rmtree(ticket_path)

        # Make the third post attempt
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        time.sleep(10)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        more_updated_response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}).json()

        another_updated_repo_name_list = [repo['title'] for repo in more_updated_response_json]
        self.assertIn(second_duplicate_title, another_updated_repo_name_list)

        delete_github_repo('presqt-test-user', duplicate_title,
                           {'Authorization': 'token {}'.format(self.token)})
        delete_github_repo('presqt-test-user', second_duplicate_title,
                           {'Authorization': 'token {}'.format(self.token)})
        # Delete upload folder
        shutil.rmtree(ticket_path)

    def test_400_error_bad_request(self):
        """
        If the user attempts to post to an existing repo, return a 400.
        """
        # Attempt to post to an existing repo.
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(self.url + ('209372336/'),
                                    {'presqt-file': open(self.file, 'rb')}, **self.headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        time.sleep(10)

        upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 400)
        self.assertEqual(upload_job_response.data['message'],
                         "Can't upload to an existing Github repository.")

        # Delete upload folder
        shutil.rmtree(ticket_path)

    def test_401_unauthorized_user(self):
        """
        If a user does not have a valid GitHub API token, we should return a 401 unauthorized status.
        """
        headers = {'HTTP_PRESQT_DESTINATION_TOKEN': 'eggyboi',
                  'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')}, **headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        time.sleep(10)

        upload_job_response = self.client.get(response.data['upload_job'], **headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 401)
        self.assertEqual(upload_job_response.data['message'],
                         'The response returned a 401 unauthorized status code.')

        # Delete upload folder
        shutil.rmtree(ticket_path)

    def test_400_bad_bag_format(self):
        """
        Test that we get 400 bad request status' when the bag to upload is not formatted correctly.
        """
        # First test is of multiple directories
        bad_bag = 'presqt/api_v1/tests/resources/upload/BadProjectMultipleFolders.zip'
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(self.url, {'presqt-file': open(bad_bag, 'rb')}, **self.headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        time.sleep(10)

        upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 400)
        self.assertEqual(upload_job_response.data['message'],
                         'Repository is not formatted correctly. Multiple directories exist at the top level.')

        # Delete the upload folder
        shutil.rmtree(ticket_path)

        # Files at top level test
        # First test is of multiple directories
        bad_bag = 'presqt/api_v1/tests/resources/upload/SingleFileDuplicate.zip'
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(self.url, {'presqt-file': open(bad_bag, 'rb')}, **self.headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        time.sleep(10)

        upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 400)
        self.assertEqual(upload_job_response.data['message'],
                         'Repository is not formatted correctly. Files exist at the top level.')

        # Delete the upload folder
        shutil.rmtree(ticket_path)

    def test_500_server_error(self):
        """
        If GitHub is having server issues, we want to make the user aware.
        """
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        with patch('requests.post') as fake_post:
            fake_post.return_value = mock_req

            self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
            response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')},
                                    **self.headers)

            ticket_number = response.data['ticket_number']
            ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

            time.sleep(10)

            upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
            self.assertEqual(upload_job_response.data['status_code'], 400)
            self.assertEqual(upload_job_response.data['message'],
                             'Response has status code 500 while creating repository {}'.format(
                                 self.repo_title))

            # Delete the upload folder
            shutil.rmtree(ticket_path)
