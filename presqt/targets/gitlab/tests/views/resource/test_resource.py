import json
import shutil
import base64
import requests
from unittest.mock import patch

from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from django.test import SimpleTestCase

from config.settings.base import GITLAB_TEST_USER_TOKEN, GITLAB_UPLOAD_TEST_USER_TOKEN
from presqt.targets.gitlab.utilities import delete_gitlab_project
from presqt.targets.gitlab.functions.upload_metadata import gitlab_upload_metadata
from presqt.targets.utilities.tests.shared_upload_test_functions import \
    (shared_upload_function_gitlab, process_wait)
from presqt.utilities import read_file, PresQTError


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
        resource_id = '17433066:dangles%2Ejson'
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


class TestResourcePOST(SimpleTestCase):
    """
    Test the endpoint's POST method for resource uploads:
         `api_v1/targets/{target_name}/resources/{resource_id}/`
         `api_v1/targets/{target_name}/resources/`

    Testing Gitlab integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.token = GITLAB_UPLOAD_TEST_USER_TOKEN
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': self.token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        self.resource_id = None
        self.duplicate_action = 'ignore'
        self.url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.resources_ignored = []
        self.resources_updated = []
        self.hash_algorithm = 'sha256'
        self.success_message = 'Upload successful.'

    def test_success_upload_to_existing_containers(self):
        """
        Test that we can successfully upload to existing containers in Gitlab.
        """
        shared_upload_function_gitlab(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        project_id = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_UPLOAD_TEST_USER_TOKEN}).json()[0]['id']
        shutil.rmtree(self.ticket_path)

        # Upload to existing repo
        self.resource_id = project_id
        self.url = reverse('resource', kwargs={'target_name': 'gitlab', 'resource_id': project_id})
        shared_upload_function_gitlab(self)
        shutil.rmtree(self.ticket_path)

        # Attempt to upload a duplicate resource
        self.resource_id = project_id
        self.resources_ignored = [
            '/NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png']
        self.url = reverse('resource', kwargs={'target_name': 'gitlab', 'resource_id': project_id})
        shared_upload_function_gitlab(self)
        shutil.rmtree(self.ticket_path)

        # Upload to existing folder
        self.resource_id = '{}:funnyfunnyimages'.format(project_id)
        self.success_message = "Upload successful."
        self.resources_ignored = []
        self.url = reverse('resource', kwargs={
                           'target_name': 'gitlab', 'resource_id': self.resource_id})
        shared_upload_function_gitlab(self)
        shutil.rmtree(self.ticket_path)

        # Delete upload folder and project
        delete_gitlab_project(project_id, GITLAB_UPLOAD_TEST_USER_TOKEN)

    def test_error_upload_to_file(self):
        """
        Test that we will get an error when attempting to upload to a file.
        """
        shared_upload_function_gitlab(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        project_id = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_UPLOAD_TEST_USER_TOKEN}).json()[0]['id']
        shutil.rmtree(self.ticket_path)

        # Upload to existing repo
        self.resource_id = '{}:funnyfunnyimages%2FScreen Shot 2019-07-15 at 3%2E26%2E49 PM%2Epng'.format(
            project_id)
        self.url = reverse('resource', kwargs={
                           'target_name': 'gitlab', 'resource_id': self.resource_id})
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(self.url, {'presqt-file': open(
            self.file, 'rb')}, **self.headers)

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
            process_info['message'], 'Resource with id, {}, belongs to a file.'.format(self.resource_id))
        self.assertEqual(process_info['status_code'], 400)

        shutil.rmtree(self.ticket_path)

        # Delete upload folder and project
        delete_gitlab_project(project_id, GITLAB_UPLOAD_TEST_USER_TOKEN)

    def test_duplicate_update(self):
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectSingleFileToUpload.zip'
        shared_upload_function_gitlab(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        project_id = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_UPLOAD_TEST_USER_TOKEN}).json()[0]['id']
        shutil.rmtree(self.ticket_path)

        self.file = 'presqt/api_v1/tests/resources/upload/ProjectSingleDuplicateFileToUpload.zip'
        self.resource_id = project_id
        self.duplicate_action = 'update'
        self.resources_updated = ['/Screen Shot 2019-07-15 at 3.51.13 PM.png']
        self.url = reverse('resource', kwargs={
                           'target_name': 'gitlab', 'resource_id': self.resource_id})
        shared_upload_function_gitlab(self)
        shutil.rmtree(self.ticket_path)

        # Delete upload folder and project
        delete_gitlab_project(project_id, GITLAB_UPLOAD_TEST_USER_TOKEN)

    def test_error_bad_project_id(self):
        self.url = reverse('resource', kwargs={
                           'target_name': 'gitlab', 'resource_id': 'badbadbadidnowaythisisreal'})

        response = self.client.post(
            self.url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

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
        process_info = read_file('{}/process_info.json'.format(self.ticket_path), True)
        self.assertEquals(
            process_info['message'], "Project with id, badbadbadidnowaythisisreal, could not be found.")
        self.assertEquals(process_info['status_code'], 404)

        shutil.rmtree(self.ticket_path)

    def test_upload_to_project_with_invalid_metadata(self):
        """
        If a project has invalid metadata, we need to change the name and create a new metadata file.
        """
        shared_upload_function_gitlab(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        project_id = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_UPLOAD_TEST_USER_TOKEN}).json()[0]['id']
        shutil.rmtree(self.ticket_path)

        put_url = "https://gitlab.com/api/v4/projects/{}/repository/files/PRESQT_FTS_METADATA%2Ejson".format(
            project_id)

        # Update metadata to be invalid for testing purposes.
        metadata_dict = json.dumps({"bad_metadata": "metadata"}, indent=4).encode('utf-8')
        encoded_file = base64.b64encode(metadata_dict)

        data = {"branch": "master",
                "commit_message": "Made it bad...",
                "encoding": "base64",
                "content": encoded_file}

        requests.put(put_url, headers={'Private-Token': GITLAB_UPLOAD_TEST_USER_TOKEN}, data=data)

        self.resource_id = project_id
        self.url = reverse('resource', kwargs={
                           'target_name': 'gitlab', 'resource_id': self.resource_id})
        shared_upload_function_gitlab(self)

        shutil.rmtree(self.ticket_path)
        # Delete upload folder and project
        delete_gitlab_project(project_id, GITLAB_UPLOAD_TEST_USER_TOKEN)

    def test_upload_to_existing_project_valid_metadata_error(self):
        """
        Test that an error is raised if there's an issue updating a valid metadata file.
        """
        # Mock a server error for when a put request is made.
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        shared_upload_function_gitlab(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        project_id = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_UPLOAD_TEST_USER_TOKEN}).json()[0]['id']
        shutil.rmtree(self.ticket_path)

        # Now I'll make an explicit call to our metadata function with a mocked server error and ensure
        # it is raising an exception.
        with patch('requests.put') as mock_request:
            mock_request.return_value = mock_req
            # Attempt to update the metadata, but the server is down!
            self.assertRaises(PresQTError, gitlab_upload_metadata, self.token, project_id,
                              {"context": {}, "allKeywords": [], "actions": []})

        # Delete upload folder and project
        delete_gitlab_project(project_id, GITLAB_UPLOAD_TEST_USER_TOKEN)

    def test_upload_to_existing_project_invalid_metadata_error(self):
        """
        Test that an error is raised if there's an issue updating an invalid metadata file.
        """
        # Mock a server error for when a post request is made.
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        shared_upload_function_gitlab(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        project_id = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_UPLOAD_TEST_USER_TOKEN}).json()[0]['id']
        shutil.rmtree(self.ticket_path)

        put_url = "https://gitlab.com/api/v4/projects/{}/repository/files/PRESQT_FTS_METADATA%2Ejson".format(
            project_id)

        # Update metadata to be invalid for testing purposes.
        metadata_dict = json.dumps({"bad_metadata": "metadata"}, indent=4).encode('utf-8')
        encoded_file = base64.b64encode(metadata_dict)

        data = {"branch": "master",
                "commit_message": "Made it bad...",
                "encoding": "base64",
                "content": encoded_file}

        requests.put(put_url, headers={'Private-Token': GITLAB_UPLOAD_TEST_USER_TOKEN}, data=data)

        # Now I'll make an explicit call to our metadata function with a mocked server error and ensure
        # it is raising an exception.
        with patch('requests.post') as mock_request:
            mock_request.return_value = mock_req
            # Attempt to update the metadata, but the server is down!
            self.assertRaises(PresQTError, gitlab_upload_metadata, self.token, project_id,
                              {"context": {}, "actions": []})

        # Delete upload folder and project
        delete_gitlab_project(project_id, GITLAB_UPLOAD_TEST_USER_TOKEN)

    def test_try_upload_same_duplicate(self):
        shared_upload_function_gitlab(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        project_id = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_UPLOAD_TEST_USER_TOKEN}).json()[0]['id']
        self.resource_id = project_id
        shutil.rmtree(self.ticket_path)

        self.url = reverse('resource', kwargs={'target_name': 'gitlab', 'resource_id': self.resource_id})
        shared_upload_function_gitlab(self)

        shutil.rmtree(self.ticket_path)

        self.duplicate_action = 'update'
        self.url = reverse('resource', kwargs={'target_name': 'gitlab', 'resource_id': self.resource_id})
        self.resources_ignored = ["/NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png"]
        shared_upload_function_gitlab(self)
        shutil.rmtree(self.ticket_path)

        # Delete upload folder and project
        delete_gitlab_project(project_id, GITLAB_UPLOAD_TEST_USER_TOKEN)

    def test_success_202_empty_folder(self):
        """
        If an empty directory is included in the uploaded project, we want to ensure the user is
        made aware.
        """
        # 202 when uploading a new top level repo
        shared_upload_function_gitlab(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        project_id = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_UPLOAD_TEST_USER_TOKEN}).json()[0]['id']
        shutil.rmtree(self.ticket_path)

        self.file = 'presqt/api_v1/tests/resources/upload/Empty_Directory_Bag.zip'
        self.resources_ignored = ['/Egg/Empty_Folder']
        self.resource_id = project_id
        self.url = reverse('resource', kwargs={'target_name': 'gitlab', 'resource_id': self.resource_id})
        shared_upload_function_gitlab(self)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

        # Delete upload folder and project
        delete_gitlab_project(project_id, GITLAB_UPLOAD_TEST_USER_TOKEN)

    def test_failed_upload_to_existing_project(self):
        # Mock a server error for when a put request is made.
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        # 202 when uploading a new top level repo
        shared_upload_function_gitlab(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        project_id = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_UPLOAD_TEST_USER_TOKEN}).json()[0]['id']
        self.resource_id = project_id
        shutil.rmtree(self.ticket_path)

        # Now I'll make an explicit call to our metadata function with a mocked server error and ensure
        # it is raising an exception.
        with patch('requests.post') as mock_request:
            mock_request.return_value = mock_req

            # Upload to the newly created project
            self.url = reverse('resource', kwargs={'target_name': 'gitlab', 'resource_id': project_id})
            self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
            response = self.client.post(self.url, {'presqt-file': open(
                self.file, 'rb')}, **self.headers)

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
            self.assertEqual(process_info['message'], "Upload failed with a status code of 500")
            self.assertEqual(process_info['status_code'], 400)

            # Delete upload folder
            shutil.rmtree(self.ticket_path)

            # Delete GitLab Project
            delete_gitlab_project(project_id, GITLAB_UPLOAD_TEST_USER_TOKEN)