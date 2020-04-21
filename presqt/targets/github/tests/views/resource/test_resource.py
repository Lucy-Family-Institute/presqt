import base64
import json
import shutil
from unittest.mock import patch

import requests
from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import GITHUB_TEST_USER_TOKEN
from presqt.targets.github.functions.upload_metadata import github_upload_metadata
from presqt.targets.github.utilities import delete_github_repo
from presqt.targets.utilities import shared_upload_function_github, process_wait
from presqt.utilities import read_file, PresQTError


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
        for key in extra_keys:
            self.assertIn(key, list(response.data['extra'].keys()))
        # Spot check some individual fields
        self.assertEqual('repo', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('ProjectTwo', response.data['title'])
        # Download Link
        self.assertEqual(len(response.data['links']), 3)

    def test_success_file(self):
        """
        Returns a 200 if the GET method is successful when getting a GitHub `file`.
        """
        resource_id = '209373787:README%2Emd'
        url = reverse('resource', kwargs={'target_name': 'github',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)

    def test_success_folder(self):
        """
        Returns a 200 if the GET method is successful when getting a GitHub `folder`.
        """
        resource_id = '209373160:album_uploader'
        url = reverse('resource', kwargs={'target_name': 'github',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)

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
            response.data, {'error': "Token is invalid. Response returned a 401 status code."})


class TestResourcePOST(SimpleTestCase):
    """
    Test the endpoint's POST method for resource uploads:
         `api_v1/targets/{target_name}/resources/{resource_id}/`
         `api_v1/targets/{target_name}/resources/`

    Testing Github integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.token = GITHUB_TEST_USER_TOKEN
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': self.token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        self.good_zip_file = 'presqt/api_v1/tests/resources/upload/GoodBagIt.zip'
        self.repo_title = 'NewProject'

        self.resource_id = None
        self.duplicate_action = 'ignore'
        self.url = reverse('resource_collection', kwargs={'target_name': 'github'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.resources_ignored = []
        self.failed_fixity = ['/NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png']
        self.resources_updated = []
        self.hash_algorithm = 'md5'

    def tearDown(self):
        """
        This should run at the end of this test class
        """
        delete_github_repo('presqt-test-user', self.repo_title,
                           {'Authorization': 'token {}'.format(GITHUB_TEST_USER_TOKEN)})

    def test_success_202_upload_to_existing_project(self):
        """
        Return a 202 when a file is uploading.
        """
        # 202 when uploading a new top level repo
        shared_upload_function_github(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        response_json = self.client.get(
            self.url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}).json()

        repo_exists = False
        repo_id = None

        for repo in response_json:
            if repo['title'] == self.repo_title:
                repo_exists = True
                repo_id = repo['id']

        self.assertEquals(True, repo_exists)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

        # Upload to the newly created project
        self.url = reverse('resource', kwargs={'target_name': 'github', 'resource_id': repo_id})
        shared_upload_function_github(self)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

        # Try the same upload again so we get a resource ignored
        self.url = reverse('resource', kwargs={'target_name': 'github', 'resource_id': repo_id})
        self.resources_ignored = ['/NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png']
        self.failed_fixity = []
        shared_upload_function_github(self)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

        # Try the same upload again but with duplicate resources set to update
        self.duplicate_action = 'update'
        self.url = reverse('resource', kwargs={'target_name': 'github', 'resource_id': repo_id})
        self.resources_updated = ['/NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png']
        self.failed_fixity = ['/NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png']
        self.resources_ignored = []
        shared_upload_function_github(self)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

        # Upload to an existing folder
        self.url = reverse('resource', kwargs={'target_name': 'github', 'resource_id': '{}:NewProject%2Efunnyfunnyimages'.format(repo_id)})
        self.resources_ignored = []
        self.resources_updated = []
        self.failed_fixity = ['/NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png']
        shared_upload_function_github(self)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

    def test_success_bad_id_upload_existing_project(self):
        """
        Return a 202 when a file is uploading.
        """
        # 202 when uploading a new top level repo
        shared_upload_function_github(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        self.client.get(
            self.url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}).json()

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

        self.url = reverse('resource', kwargs={'target_name': 'github', 'resource_id': '58435738573489573498573498573'})
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

        ticket_number = response.data['ticket_number']
        self.ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Verify status code and message
        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.data['message'], 'The server is processing the request.')

        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(self.ticket_path), True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the spawned off process finishes in the background to do further validation
        process_wait(process_info, self.ticket_path)

        # Verify process_info.json file data
        process_info = read_file('{}/process_info.json'.format(self.ticket_path), True)
        self.assertEqual(process_info['status'], 'failed')
        self.assertEqual(
            process_info['message'],
            "The resource with id, 58435738573489573498573498573, does not exist for this user.")
        self.assertEqual(process_info['status_code'], 404)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

    def test_success_empty_directory(self):
        """
        Return a 202 when a file is uploading.
        """
        # 202 when uploading a new top level repo
        shared_upload_function_github(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        response_json = self.client.get(
            self.url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}).json()

        repo_exists = False
        repo_id = None

        for repo in response_json:
            if repo['title'] == self.repo_title:
                repo_exists = True
                repo_id = repo['id']

        self.assertEquals(True, repo_exists)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)
        self.file = 'presqt/api_v1/tests/resources/upload/Empty_Directory_Bag.zip'
        self.failed_fixity = ['/Egg/egg.json']
        self.resources_ignored = ['/Egg/Empty_Folder']
        self.url = reverse('resource', kwargs={'target_name': 'github', 'resource_id': repo_id})
        shared_upload_function_github(self)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

    def test_bad_metadata_request(self):
        """
        Ensure that an error is returned if Github doesn't return a 201 status code.
        """
        self.assertRaises(PresQTError, github_upload_metadata, self.token, 'eggtest',
                      {"bad": "metadata"})

    def test_error_updating_metadata_file(self):
        """
        Test that an error is raised if there's an issue creating an invalid metadata file.
        """
        # Mock a server error for when a put request is made.
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        self.resource_id = None
        self.duplicate_action = 'ignore'
        self.url = reverse('resource_collection', kwargs={'target_name': 'github'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.resources_ignored = []
        self.resources_updated = []
        self.hash_algorithm = 'md5'
        shared_upload_function_github(self)


        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        response_json = self.client.get(
            self.url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}).json()

        for repo in response_json:
            if repo['title'] == self.repo_title:
                repo_name = repo['title']

        # Now I'll make an explicit call to our metadata function with a mocked server error and ensure
        # it is raising an exception.
        with patch('requests.put') as mock_request:
            mock_request.return_value = mock_req
            # Attempt to update the metadata, but the server is down!
            self.assertRaises(PresQTError, github_upload_metadata, self.token, repo_name,
                              {"context": {}, "actions": []})

        # Delete corresponding folder
        shutil.rmtree(self.ticket_path)

    def test_error_updating_invalid_metadata_file(self):
        """
        Test that an error is raised if there's an issue creating an invalid metadata file.
        """
        # Mock a server error for when a put request is made.
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        self.resource_id = None
        self.duplicate_action = 'ignore'
        self.url = reverse('resource_collection', kwargs={'target_name': 'github'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.resources_ignored = []
        self.resources_updated = []
        self.hash_algorithm = 'md5'
        shared_upload_function_github(self)


        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        response_json = self.client.get(
            self.url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN}).json()

        for repo in response_json:
            if repo['title'] == self.repo_title:
                repo_name = repo['title']
        metadata_file_get = requests.get("https://api.github.com/repos/presqt-test-user/{}/contents/PRESQT_FTS_METADATA.json".format(repo_name))

        # Update metadata to be invalid for testing purposes.
        metadata_dict = json.dumps({"bad_metadata":"metadata"}, indent=4).encode('utf-8')
        encoded_file = base64.b64encode(metadata_dict).decode('utf-8')

        data = {
            "message": "PresQT Upload",
            "sha": metadata_file_get.json()['sha'],
            "committer": {
                "name": "PresQT",
                "email": "N/A"},
            "content": encoded_file}

        requests.put("https://api.github.com/repos/presqt-test-user/{}/contents/PRESQT_FTS_METADATA.json".format(repo_name),
                                headers={"Authorization": "token {}".format(GITHUB_TEST_USER_TOKEN)},
                                data=json.dumps(data))

        # Now I'll make an explicit call to our metadata function with a mocked server error and ensure
        # it is raising an exception.
        with patch('requests.put') as mock_request:
            mock_request.return_value = mock_req
            # Attempt to update the metadata, but the server is down!
            self.assertRaises(PresQTError, github_upload_metadata, self.token, repo_name,
                              {"context": {}, "actions": []})

        # Delete corresponding folder
        shutil.rmtree(self.ticket_path)