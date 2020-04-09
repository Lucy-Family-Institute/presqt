import base64
import json
import shutil
from unittest.mock import patch

import requests
from django.test import SimpleTestCase
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from config.settings.base import GITLAB_TEST_USER_TOKEN, GITLAB_UPLOAD_TEST_USER_TOKEN
from presqt.targets.gitlab.functions.upload_metadata import gitlab_upload_metadata
from presqt.targets.gitlab.utilities import delete_gitlab_project
from presqt.targets.utilities.tests.shared_upload_test_functions import \
    shared_upload_function_gitlab
from presqt.utilities import PresQTError, read_file


class TestResourceCollection(SimpleTestCase):
    """
    Test the 'api_v1/targets/gitlab/resources' endpoint's GET method.

    Testing GitLab integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_TEST_USER_TOKEN}

    def test_success_gitlab(self):
        """
        Return a 200 if the GET method is successful when grabbing GitLab resources.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))
        # Verify the count of resource objects is what we expect.
        self.assertEqual(len(response.data), 21)

        for data in response.data:
            self.assertEqual(len(data['links']), 1)

    def test_success_gitlab_with_search(self):
        """
        Return a 200 if the GET method is successful when grabbing GitLab resources with search
        parameters.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response = self.client.get(url + '?title=A+Good+Egg', **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))


        ###### Search by ID #######
        response = self.client.get(url + '?id=17990806', **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))

        #### Search by Author ####
        response = self.client.get(url + '?author=prometheus-test', **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))

        ### Search by General ###
        response = self.client.get(url + '?general=egg', **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))

    def test_error_400_missing_token_gitlab(self):
        """
        Return a 400 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response = self.client.get(url)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "PresQT Error: 'presqt-source-token' missing in the request headers."})

    def test_error_401_invalid_token_gitlab(self):
        """
        Return a 401 if the token provided is not a valid token.
        """
        client = APIClient()
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'eggyboi'}
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response = client.get(url, **header)
        # Verify the error status code and message.
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "Token is invalid. Response returned a 401 status code."})

    def test_error_400_bad_search_parameters(self):
        """
        Test for a 400 with a bad parameter
        """
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        # TOO MANY KEYS
        response = self.client.get(url + '?title=hat&spaghetti=egg', **self.header)

        self.assertEqual(response.data['error'], 'PresQT Error: The search query is not formatted correctly.')
        self.assertEqual(response.status_code, 400)

        # BAD KEY
        response = self.client.get(url + '?spaghetti=egg', **self.header)

        self.assertEqual(response.data['error'], 'PresQT Error: GitLab does not support spaghetti as a search parameter.')
        self.assertEqual(response.status_code, 400)

        # SPECIAL CHARACTERS IN REQUEST
        response = self.client.get(url + '?title=egg:boi', **self.header)

        self.assertEqual(response.data['error'], 'PresQT Error: The search query is not formatted correctly.')
        self.assertEqual(response.status_code, 400)

    def test_for_id_search_no_results_gitlab(self):
        """
        Test for a successful id search but for an id that doesn't exist
        """
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response = self.client.get(url + '?id=supasupabadid', **self.header)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_for_author_search_no_results_gitlab(self):
        """
        Test for a successful author search but for an author that doesn't exist
        """
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response = self.client.get(url + '?author=XxsupasupasupasupabadauthorxX', **self.header)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])


class TestResourceCollectionPOST(SimpleTestCase):
    """
    Test the endpoint's POST method for resource uploads:
         `api_v1/targets/{target_name}/resources/{resource_id}/`
         `api_v1/targets/{target_name}/resources/`

    Testing GitLab integration.
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


    def test_success_202_upload(self):
        """
        Return a 202 when a file is uploading.
        """
        # 202 when uploading a new top level repo
        shared_upload_function_gitlab(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_UPLOAD_TEST_USER_TOKEN}).json()

        # Delete upload folder and project
        shutil.rmtree(self.ticket_path)
        delete_gitlab_project(response_json[0]['id'], GITLAB_UPLOAD_TEST_USER_TOKEN)

    def test_presqt_fts_metadata(self):
        """
        Check that the PRESQT_FTS_METADATA is created and what we expect.
        """
        # 202 when uploading a new top level repo
        shared_upload_function_gitlab(self)
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_UPLOAD_TEST_USER_TOKEN}).json()

        # On the project that was just created, we need to get the contents of the metadata file.
        metadata_link = 'https://gitlab.com/api/v4/projects/{}/repository/files/PRESQT_FTS_METADATA%2Ejson?ref=master'.format(response_json[0]['id'])

        # Get the metadata json
        response = requests.get(metadata_link, headers={"Private-Token": "{}".format(self.token)})
        metadata_file = json.loads(base64.b64decode(response.json()['content']))

        # Action metadata
        self.assertEqual(metadata_file['actions'][0]['actionType'], 'resource_upload')
        self.assertEqual(metadata_file['actions'][0]['sourceTargetName'], 'Local Machine')
        self.assertEqual(metadata_file['actions'][0]['destinationTargetName'], 'gitlab')
        self.assertEqual(metadata_file['actions'][0]['destinationUsername'], 'Prometheus-Upload')

        # File metadata
        self.assertEqual(metadata_file['actions'][0]['files']['created'][0]['title'],
                         'Screen Shot 2019-07-15 at 3.26.49 PM.png')
        self.assertEqual(metadata_file['actions'][0]['files']['created'][0]['sourcePath'],
                         '/NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png')
        self.assertEqual(metadata_file['actions'][0]['files']['created'][0]['destinationPath'],
                         'NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png')
        self.assertEqual(metadata_file['actions'][0]['files']['created'][0]['destinationHashes'],
                         {'sha256': '6d33275234b28d77348e4e1049f58b95a485a7a441684a9eb9175d01c7f141ea'})

        # Delete upload folder
        shutil.rmtree(self.ticket_path)
        delete_gitlab_project(response_json[0]['id'], GITLAB_UPLOAD_TEST_USER_TOKEN)

    def test_bad_metadata_request(self):
        """
        Ensure that the proper error is raised when we get a non-201 response from GitLab.
        """
        # Calling this function manually to confirm explicit error is raised.
        self.assertRaises(PresQTError, gitlab_upload_metadata, self.token, "BAD", {"fake": "data"})

    def test_upload_with_invalid_metadata_file_and_valid_metadata(self):
        """
        If the upload file contains an invalid metadata file, it needs to be renamed and a new metadata
        file is to be made. If it is valid, we need to append the new action.
        """
        header = {"Private-Token": "{}".format(self.token)}
        bag_with_bad_metadata = 'presqt/api_v1/tests/resources/upload/Invalid_Metadata_Upload.zip'
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(self.url, {'presqt-file': open(bag_with_bad_metadata, 'rb')},
                                    **self.headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        # On the project that was just created, we need to get the contents of the invalid metadata file.
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_UPLOAD_TEST_USER_TOKEN}).json()

        # On the project that was just created, we need to get the contents of the metadata file.
        metadata_link = 'https://gitlab.com/api/v4/projects/{}/repository/files/INVALID_PRESQT_FTS_METADATA%2Ejson?ref=master'.format(response_json[0]['id'])

        # Get the metadata json
        response = requests.get(metadata_link, headers={"Private-Token": "{}".format(self.token)})
        invalid_metadata_file = json.loads(base64.b64decode(response.json()['content']))

        self.assertEqual(invalid_metadata_file, {'invalid_metadata': 'no bueno'})

        delete_gitlab_project(response_json[0]['id'], GITLAB_UPLOAD_TEST_USER_TOKEN)
        # Delete upload folder
        shutil.rmtree(ticket_path)

        ###### VALID METADATA #######
        bag_with_good_metadata = 'presqt/api_v1/tests/resources/upload/Valid_Metadata_Upload.zip'
        response = self.client.post(self.url, {'presqt-file': open(bag_with_good_metadata, 'rb')},
                                    **self.headers)
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass
        response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_UPLOAD_TEST_USER_TOKEN}).json()

        # On the project that was just created, we need to get the contents of the metadata file.
        metadata_link = 'https://gitlab.com/api/v4/projects/{}/repository/files/PRESQT_FTS_METADATA%2Ejson?ref=master'.format(response_json[0]['id'])

        # Get the metadata json
        response = requests.get(metadata_link, headers={"Private-Token": "{}".format(self.token)})
        valid_metadata_file = json.loads(base64.b64decode(response.json()['content']))

        self.assertEqual(len(valid_metadata_file['actions']), 2)

        delete_gitlab_project(response_json[0]['id'], GITLAB_UPLOAD_TEST_USER_TOKEN)
        # Delete upload folder
        shutil.rmtree(ticket_path)

    def test_400_error_bad_request(self):
        """
        If the user attempts to post to an existing project, return a 400.
        """
        # Attempt to post to an existing repo.
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(self.url + ('209372336/'),
                                    {'presqt-file': open(self.file, 'rb')}, **self.headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 400)
        self.assertEqual(upload_job_response.data['message'],
                         "Can't upload to an existing GitLab repository.")

        # Delete upload folder
        shutil.rmtree(ticket_path)

    def test_401_unauthorized_user(self):
        """
        If a user does not have a valid GitLab API token, we should return a 401 unauthorized status.
        """
        headers = {'HTTP_PRESQT_DESTINATION_TOKEN': 'eggyboi',
                   'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')}, **headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_job_response = self.client.get(response.data['upload_job'], **headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 401)
        self.assertEqual(upload_job_response.data['message'],
                         'Token is invalid. Response returned a 401 status code.')

        # Delete upload folder
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

            # Wait until the spawned off process finishes in the background
            # to do validation on the resulting files
            process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            while process_info['status'] == 'in_progress':
                try:
                    process_info = read_file('{}/process_info.json'.format(ticket_path), True)
                except json.decoder.JSONDecodeError:
                    # Pass while the process_info file is being written to
                    pass

            upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
            self.assertEqual(upload_job_response.data['status_code'], 400)

            # Delete the upload folder
            shutil.rmtree(ticket_path)

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
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_job_response = self.client.get(response.data['upload_job'], **self.headers)

        # Verify status code and message
        self.assertEqual(upload_job_response.data['resources_ignored'], ['/Egg/Empty_Folder'])

        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_UPLOAD_TEST_USER_TOKEN}).json()
        delete_gitlab_project(response_json[0]['id'], GITLAB_UPLOAD_TEST_USER_TOKEN)

        # Delete upload folder
        shutil.rmtree(ticket_path)