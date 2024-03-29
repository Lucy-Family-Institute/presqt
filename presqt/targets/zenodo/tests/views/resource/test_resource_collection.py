import json
import requests
import shutil
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import ZENODO_TEST_USER_TOKEN
from presqt.targets.utilities import shared_upload_function_osf
from presqt.targets.zenodo.functions.upload_metadata import zenodo_upload_metadata
from presqt.utilities import read_file, PresQTError
from presqt.api_v1.utilities import hash_tokens


class TestResourceCollection(SimpleTestCase):
    """
    Test the 'api_v1/targets/zenodo/resources' endpoint's GET method.

    Testing Zenodo integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': ZENODO_TEST_USER_TOKEN}

    def test_success_zenodo(self):
        """
        Return a 200 if the GET method is successful when grabbing Zenodo resources.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'zenodo'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data['resources']:
            self.assertEqual(len(data['links']), 1)
            self.assertListEqual(keys, list(data.keys()))
        # Verify the count of resource objects is what we expect.
        # Note: We are only getting the top level resources
        self.assertEqual(len(response.data['resources']), 2)

    def test_success_zenodo_page_1(self):
        """
        Return a 200 if the GET method is successful when grabbing Zenodo resources.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'zenodo'})
        response = self.client.get(url + "?page=1", **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data['resources']:
            self.assertEqual(len(data['links']), 1)
            self.assertListEqual(keys, list(data.keys()))
        # Verify the count of resource objects is what we expect.
        self.assertEqual(response.data['pages']['total_pages'], 1)

    def test_success_zenodo_with_search(self):
        """
        Return a 200 if the GET method is successful when grabbing Zenodo resources.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'zenodo'})
        response = self.client.get(url + "?title=a+curious+egg", **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data['resources']:
            self.assertListEqual(keys, list(data.keys()))

        # Search by ID
        response = self.client.get(url + "?id=3723281", **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data['resources']:
            self.assertListEqual(keys, list(data.keys()))

        # Search by General
        response = self.client.get(url + "?general=eggs", **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data['resources']:
            self.assertListEqual(keys, list(data.keys()))

        # Search by Keywords
        response = self.client.get(url + "?keywords=egg", **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data['resources']:
            self.assertListEqual(keys, list(data.keys()))

    def test_error_400_missing_token_zenodo(self):
        """
        Return a 400 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'zenodo'})
        response = self.client.get(url)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "PresQT Error: 'presqt-source-token' missing in the request headers."})

    def test_error_401_invalid_token_zenodo(self):
        """
        Return a 401 if the token provided is not a valid token.
        """
        client = APIClient()
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'eggyboi'}
        url = reverse('resource_collection', kwargs={'target_name': 'zenodo'})
        response = client.get(url, **header)
        # Verify the error status code and message.
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "Token is invalid. Response returned a 401 status code."})


class TestResourceCollectionPOST(SimpleTestCase):
    """
    Test the endpoint's POST method for resource uploads:
         `api_v1/targets/{target_name}/resources/{resource_id}/`
         `api_v1/targets/{target_name}/resources/`

    Testing Zenodo integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.token = ZENODO_TEST_USER_TOKEN
        self.ticket_number = hash_tokens(self.token)
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': self.token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore',
                        'HTTP_PRESQT_EMAIL_OPT_IN': ''}
        self.project_title = 'NewProject'
        self.resource_id = None
        self.duplicate_action = 'ignore'
        self.url = reverse('resource_collection', kwargs={'target_name': 'zenodo'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.resources_ignored = []
        self.resources_updated = []
        self.hash_algorithm = 'md5'
        self.auth_params = {'access_token': self.token}
        self.metadata_dict = {
            "allKeywords": [],
            "actions": [
                {
                    "id": "uuid",
                    "actionDateTime": "2019-11-11 15:18:39.596797+00:00",
                    "actionType": "resource_upload",
                    "sourceTargetName": "Local Machine",
                    "destinationTargetName": "zenodo",
                    "sourceUsername": "TestUser",
                    "destinationUsername": "81621",
                    "keywords": {},
                    "files": {
                        "created": [],
                        "updated": [],
                        "ignored":[]
                    }
                }
            ]
        }

    def tearDown(self):
        """
        Delete the uploaded test files.
        """
        test_user_projects = requests.get('https://zenodo.org/api/deposit/depositions',
                                          params=self.auth_params).json()
        for project in test_user_projects:
            if project['title'] == self.project_title:
                requests.delete(project['links']['self'], params=self.auth_params)

    def test_success_202_upload(self):
        """
        Return a 202 when a file is uploading.
        """
        # 202 when uploading a new top level repo
        shared_upload_function_osf(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'zenodo'})
        response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': ZENODO_TEST_USER_TOKEN}).json()['resources']

        repo_name_list = [repo['title'] for repo in response_json]
        self.assertIn(self.project_title, repo_name_list)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

        # 202 when uploading to an existing project.
        self.resource_id = [resource['id']
                            for resource in response_json if resource['title'] == self.project_title][0]
        self.duplicate_action = 'ignore'
        self.url = reverse('resource', kwargs={
                           'target_name': 'zenodo', 'resource_id': self.resource_id})
        self.file = 'presqt/api_v1/tests/resources/upload/SingleFileDuplicate.zip'
        shared_upload_function_osf(self)

        # Ensure there are two actions in the metadata.
        metadata_helper = requests.get('https://zenodo.org/api/deposit/depositions/{}/files'.format(
            self.resource_id),
            params=self.auth_params).json()
        for file in metadata_helper:
            if file['filename'] == 'PRESQT_FTS_METADATA.json':
                response = requests.get(file['links']['download'], params=self.auth_params)
                metadata_file = json.loads(response.content)

        # Verify there are multiple actions
        self.assertEqual(len(metadata_file['actions']), 2)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

    def test_uploading_to_exisitng_container_ignore(self):
        """
        If there is an ignored file from Zenodo when uploading to an existing container, we want 
        to make the user aware.
        """
        # 202 when uploading a new top level repo
        shared_upload_function_osf(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'zenodo'})
        response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': ZENODO_TEST_USER_TOKEN}).json()['resources']

        repo_name_list = [repo['title'] for repo in response_json]
        self.assertIn(self.project_title, repo_name_list)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

        self.resource_id = [resource['id']
                            for resource in response_json if resource['title'] == self.project_title][0]
        self.duplicate_action = 'ignore'
        self.url = reverse('resource', kwargs={
                           'target_name': 'zenodo', 'resource_id': self.resource_id})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectSingleFileToUpload.zip'

        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = 'ignore'
        response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')},
                                    **self.headers)

        ticket_path = 'mediafiles/jobs/{}'.format(self.ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['resource_upload']['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
        self.assertEqual(upload_job_response.data['status_code'], '200')
        self.assertEqual(upload_job_response.data['resources_ignored'], [
                         '/NewProject/NewProject.presqt.zip'])

        # Delete the upload folder
        shutil.rmtree(ticket_path)

    def test_error_uploading_to_exisitng_container(self):
        """
        If there is an error response from Zenodo when uploading to an existing container, we want 
        to make the user aware.
        """
        # 202 when uploading a new top level repo
        shared_upload_function_osf(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'zenodo'})
        response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': ZENODO_TEST_USER_TOKEN}).json()['resources']

        repo_name_list = [repo['title'] for repo in response_json]
        self.assertIn(self.project_title, repo_name_list)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

        # *Error* when uploading to an existing project.
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        self.resource_id = [resource['id']
                            for resource in response_json if resource['title'] == self.project_title][0]
        self.duplicate_action = 'ignore'
        self.url = reverse('resource', kwargs={
                           'target_name': 'zenodo', 'resource_id': self.resource_id})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectSingleFileToUpload.zip'

        with patch('requests.post') as fake_post:
            fake_post.return_value = mock_req

            self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = 'update'
            response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')},
                                        **self.headers)

            ticket_path = 'mediafiles/jobs/{}'.format(self.ticket_number)

            # Wait until the spawned off process finishes in the background
            # to do validation on the resulting files
            process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            while process_info['resource_upload']['status'] == 'in_progress':
                try:
                    process_info = read_file('{}/process_info.json'.format(ticket_path), True)
                except json.decoder.JSONDecodeError:
                    # Pass while the process_info file is being written to
                    pass

            upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
            self.assertEqual(upload_job_response.data['status_code'], 400)
            self.assertEqual(upload_job_response.data['message'],
                             'Zenodo returned an error trying to upload NewProject.presqt.zip')

            # Delete the upload folder
            shutil.rmtree(ticket_path)

    def test_error_uploading_to_exisitng_container_update(self):
        """
        If there is an error response from Zenodo when updating a file on an existing container, we 
        want to make the user aware.
        """
        # 202 when uploading a new top level repo
        shared_upload_function_osf(self)

        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'zenodo'})
        response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': ZENODO_TEST_USER_TOKEN}).json()['resources']

        repo_name_list = [repo['title'] for repo in response_json]
        self.assertIn(self.project_title, repo_name_list)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

        # *Error* when uploading to an existing project.
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        self.resource_id = [resource['id']
                            for resource in response_json if resource['title'] == self.project_title][0]
        self.duplicate_action = 'ignore'
        self.url = reverse('resource', kwargs={
                           'target_name': 'zenodo', 'resource_id': self.resource_id})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectSingleFileToUpload.zip'

        with patch('requests.delete') as fake_post:
            fake_post.return_value = mock_req

            self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = 'update'
            response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')},
                                        **self.headers)

            ticket_path = 'mediafiles/jobs/{}'.format(self.ticket_number)

            # Wait until the spawned off process finishes in the background
            # to do validation on the resulting files
            process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            while process_info['resource_upload']['status'] == 'in_progress':
                try:
                    process_info = read_file('{}/process_info.json'.format(ticket_path), True)
                except json.decoder.JSONDecodeError:
                    # Pass while the process_info file is being written to
                    pass

            upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
            self.assertEqual(upload_job_response.data['status_code'], 400)
            self.assertEqual(upload_job_response.data['message'],
                             'Zenodo returned an error trying to update NewProject.presqt.zip')

            # Delete the upload folder
            shutil.rmtree(ticket_path)

    def test_presqt_fts_metadata(self):
        """
        Check that the PRESQT_FTS_METADATA is created and what we expect.
        """
        # 202 when uploading a new top level repo
        shared_upload_function_osf(self)

        # On the project that was just created, we need to get the contents of the metadata file.
        metadata_helper = requests.get('https://zenodo.org/api/deposit/depositions',
                                       params=self.auth_params).json()
        for project in metadata_helper:
            if project['title'] == self.project_title:
                get_files = requests.get(project['links']['files'], params=self.auth_params).json()
                for file in get_files:
                    if file['filename'] == 'PRESQT_FTS_METADATA.json':
                        response = requests.get(file['links']['download'], params=self.auth_params)
                        metadata_file = json.loads(response.content)
        # Action metadata
        self.assertEqual(metadata_file['actions'][0]['actionType'], 'resource_upload')
        self.assertEqual(metadata_file['actions'][0]['sourceTargetName'], 'Server Created Zip')
        self.assertEqual(metadata_file['actions'][0]['destinationTargetName'], 'zenodo')
        self.assertEqual(metadata_file['actions'][0]['destinationUsername'], None)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)
    
    def test_presqt_fts_metadata_extra(self):
        """
        Check that the extra metadata is added to the deposition
        """
        self.file = 'presqt/api_v1/tests/resources/upload/Upload_Extra_Metadata.zip'
        self.project_title = 'Extra Eggs'
        # 202 when uploading a new top level repo
        shared_upload_function_osf(self)

        # On the project that was just created, we need to get the contents of the metadata file.
        metadata_helper = requests.get('https://zenodo.org/api/deposit/depositions',
                                       params=self.auth_params).json()
        for project in metadata_helper:
            if project['title'] == self.project_title:
                url = project['links']['self']
                get_info = requests.get(url, params=self.auth_params).json()
                break
        self.assertEqual(get_info['metadata']['description'], "There's so many eggs in here.")
        self.assertEqual(get_info['metadata']['creators'][0]['name'], "Egg Eggs")
        self.assertEqual(get_info['metadata']['title'], "Extra Eggs")

        requests.delete(url, params=self.auth_params)

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

    def test_upload_with_invalid_metadata_file_and_valid_metadata(self):
        """
        If the upload file contains an invalid metadata file, it needs to be renamed and a new metadata
        file is to be made. If it is valid, we need to append the new action.
        """
        ###### VALID METADATA #######
        bag_with_good_metadata = 'presqt/api_v1/tests/resources/upload/Valid_Metadata_Upload.zip'
        response = self.client.post(self.url, {'presqt-file': open(bag_with_good_metadata, 'rb')},
                                    **self.headers)

        ticket_path = 'mediafiles/jobs/{}'.format(self.ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['resource_upload']['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass
        # On the project that was just created, we need to get the contents of the metadata file.
        metadata_helper = requests.get('https://zenodo.org/api/deposit/depositions',
                                       params=self.auth_params).json()
        for project in metadata_helper:
            if project['title'] == 'Good_Egg':
                project_id = project['id']
                project_link_to_delete = project['links']['self']
                get_files = requests.get(project['links']['files'], params=self.auth_params).json()
                for file in get_files:
                    if file['filename'] == 'PRESQT_FTS_METADATA.json':
                        file_url = file['links']['self']
                        response = requests.get(file['links']['download'], params=self.auth_params)
                        valid_metadata_file = json.loads(response.content)
        self.assertEqual(len(valid_metadata_file['actions']), 1)

        ### EXPLICIT TEST UPLOADING UPDATED METADATA BUT THERE'S AN ERROR ###
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        with patch('requests.post') as fake_post:
            fake_post.return_value = mock_req
            self.assertRaises(PresQTError, zenodo_upload_metadata, self.token, project_id,
                              self.metadata_dict)

        ### EXPLICIT TEST UPLOADING METADATA, EXISTING FILE IS INVALID BUT THERE'S AN ERROR ###
        # Delete the existing metadata file
        requests.delete(file_url, params=self.auth_params)
        # Upload a new bad metadata file
        bad_metadata = {"bad": "metadata"}
        requests.post('https://zenodo.org/api/deposit/depositions/{}/files'.format(project_id),
                      params=self.auth_params,
                      data={'name': 'PRESQT_FTS_METADATA.json'},
                      files={'file': json.dumps(bad_metadata, indent=4).encode('utf-8')})
        with patch('requests.post') as fake_post:
            fake_post.return_value = mock_req
            self.assertRaises(PresQTError, zenodo_upload_metadata, self.token, project_id,
                              self.metadata_dict)

        ### EXPLICIT TEST UPLOADING METADATA BUT THERE'S AN ERROR ###
        with patch('requests.post') as fake_post:
            fake_post.return_value = mock_req
            self.assertRaises(PresQTError, zenodo_upload_metadata, self.token, project_id,
                              self.metadata_dict)

        # Delete this project
        requests.delete(project_link_to_delete, params=self.auth_params)

        # Delete upload folder
        shutil.rmtree(ticket_path)

    def test_bad_resource_id(self):
        """
        If the resource id given is invalid, we want to raise an error.
        """
        self.url = reverse('resource', kwargs={
                           'target_name': 'zenodo', 'resource_id': '52162'})

        response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')},
                                    **self.headers)

        ticket_path = 'mediafiles/jobs/{}'.format(self.ticket_number)
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['resource_upload']['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        details = self.client.get(response.data['upload_job'], **self.headers).data

        self.assertEqual(details['status_code'], 404)
        self.assertEqual(details['message'], "Can't find the resource with id 52162, on Zenodo")

        # Delete upload folder
        shutil.rmtree(ticket_path)

    def test_invalid_metadata_existing_on_zenodo(self):
        """
        If there is bad metadata on Zenodo already, we want to rename it and upload the good stuff.
        """
        # 202 when uploading a new top level repo
        shared_upload_function_osf(self)
        # Verify the new repo exists on the PresQT Resource Collection endpoint.
        url = reverse('resource_collection', kwargs={'target_name': 'zenodo'})
        response_json = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': ZENODO_TEST_USER_TOKEN}).json()['resources']
        self.resource_id = [resource['id']
                            for resource in response_json if resource['title'] == self.project_title][0]
        # Delete upload folder
        shutil.rmtree(self.ticket_path)

        # Muddy up the existing metadata file
        metadata_helper = requests.get(
            'https://zenodo.org/api/deposit/depositions/{}/files'.format(self.resource_id),
            params=self.auth_params).json()
        for file in metadata_helper:
            if file['filename'] == 'PRESQT_FTS_METADATA.json':
                # Delete old metadata file
                requests.delete(file['links']['self'], params=self.auth_params)
        bad_metadata = {"no": "good"}
        data = {'name': 'PRESQT_FTS_METADATA.json'}
        metadata_bytes = json.dumps(bad_metadata, indent=4).encode('utf-8')
        files = {'file': metadata_bytes}

        # Make the request
        response = requests.post('https://zenodo.org/api/deposit/depositions/{}/files'.format(self.resource_id),
                                 params=self.auth_params, data=data, files=files)

        # 202 when uploading to an existing project.
        self.duplicate_action = 'ignore'
        self.url = reverse('resource', kwargs={
            'target_name': 'zenodo', 'resource_id': self.resource_id})
        self.file = 'presqt/api_v1/tests/resources/upload/SingleFileDuplicate.zip'
        shared_upload_function_osf(self)

        # Ensure there are two actions in the metadata.
        metadata_helper = requests.get('https://zenodo.org/api/deposit/depositions/{}/files'.format(
            self.resource_id),
            params=self.auth_params).json()
        for file in metadata_helper:
            if file['filename'] == 'INVALID_PRESQT_FTS_METADATA.json':
                response = requests.get(file['links']['download'], params=self.auth_params)
                metadata_file = json.loads(response.content)

        # Verify there are multiple actions
        self.assertEqual(metadata_file, {'no': 'good'})

        # Delete upload folder
        shutil.rmtree(self.ticket_path)

    def test_401_unauthorized_user(self):
        """
        If a user does not have a valid Zenodo API token, we should return a 401 unauthorized status.
        """
        headers = {'HTTP_PRESQT_DESTINATION_TOKEN': 'eggyboi',
                   'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore',
                   'HTTP_PRESQT_EMAIL_OPT_IN': ''}
        response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')}, **headers)

        ticket_number = hash_tokens('eggyboi')
        ticket_path = 'mediafiles/jobs/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['resource_upload']['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_job_response = self.client.get(response.data['upload_job'], **headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 401)
        self.assertEqual(upload_job_response.data['message'],
                         "Token is invalid. Response returned a 401 status code.")

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

        ticket_path = 'mediafiles/jobs/{}'.format(self.ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['resource_upload']['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 400)
        self.assertEqual(upload_job_response.data['message'],
                         'PresQT Error: Repository is not formatted correctly. Multiple directories exist at the top level.')

        # Delete the upload folder
        shutil.rmtree(ticket_path)

        # Files at top level test
        # First test is of multiple directories
        bad_bag = 'presqt/api_v1/tests/resources/upload/SingleFileDuplicate.zip'
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
        response = self.client.post(self.url, {'presqt-file': open(bad_bag, 'rb')}, **self.headers)

        ticket_path = 'mediafiles/jobs/{}'.format(self.ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['resource_upload']['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 400)
        self.assertEqual(upload_job_response.data['message'],
                         'PresQT Error: Repository is not formatted correctly. Files exist at the top level.')

        # Delete the upload folder
        shutil.rmtree(ticket_path)

    def test_500_server_error(self):
        """
        If Zenodo is having server issues, we want to make the user aware.
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

            ticket_path = 'mediafiles/jobs/{}'.format(self.ticket_number)

            # Wait until the spawned off process finishes in the background
            # to do validation on the resulting files
            process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            while process_info['resource_upload']['status'] == 'in_progress':
                try:
                    process_info = read_file('{}/process_info.json'.format(ticket_path), True)
                except json.decoder.JSONDecodeError:
                    # Pass while the process_info file is being written to
                    pass

            upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
            self.assertEqual(upload_job_response.data['status_code'], 400)
            self.assertEqual(upload_job_response.data['message'],
                             'Zenodo returned a 500 status code while trying to create the project.')

            # Delete the upload folder
            shutil.rmtree(ticket_path)
