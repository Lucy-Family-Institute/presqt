import base64
import json
from time import sleep

import requests
import shutil
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import (OSF_UPLOAD_TEST_USER_TOKEN, GITHUB_TEST_USER_TOKEN,
                                  ZENODO_TEST_USER_TOKEN, OSF_TEST_USER_TOKEN)

from presqt.api_v1.utilities import transfer_target_validation
from presqt.utilities import read_file, PresQTValidationError
from presqt.targets.osf.utilities import delete_users_projects


class TestTransferJobGET(SimpleTestCase):
    """
    Test the `api_v1/transfer/<ticket_id>/` endpoint's GET method.

    Testing only PresQT core code.
    """

    def setUp(self):
        self.client = APIClient()
        self.destination_token = OSF_UPLOAD_TEST_USER_TOKEN
        self.source_token = GITHUB_TEST_USER_TOKEN
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': self.destination_token,
                        'HTTP_PRESQT_SOURCE_TOKEN': self.source_token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore',
                        'HTTP_PRESQT_KEYWORD_ACTION': 'suggest'}
        self.resource_id = '209373660'
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})

    def tearDown(self):
        """
        This should run at the end of the test class.
        """
        delete_users_projects(self.destination_token)

    def test_call_transfer_success(self):
        """
        Make a POST request to `resource` to begin transferring a resource.
        """
        response = self.client.post(self.url, data={
            "source_target_name": "github", "source_resource_id": self.resource_id}, **self.headers)
        self.ticket_number = response.data['ticket_number']
        self.process_info_path = 'mediafiles/transfers/{}/process_info.json'.format(
            self.ticket_number)
        self.transfer_job = response.data['transfer_job']
        process_info = read_file(self.process_info_path, True)

        self.assertEqual(self.transfer_job, ('http://testserver{}'.format(reverse(
            'transfer_job', kwargs={'ticket_number': self.ticket_number}))))

        response = self.client.get(self.transfer_job, **self.headers)
        self.assertEqual(response.data['message'], 'Transfer is being processed on the server')

        # Wait until the spawned off process finishes in the background
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(self.process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        self.assertNotEqual(process_info['status'], 'in_progress')

        # Check that transfer was successful
        response = self.client.get(self.transfer_job, **self.headers)
        self.assertEqual(response.data['status_code'], '200')
        # Fixity errors because we're dealing with GitHub
        self.assertEqual(response.data['message'],
                         "Transfer successful. Fixity can't be determined because GitHub may not have provided a file checksum. See PRESQT_FTS_METADATA.json for more details.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/transfers/{}'.format(self.ticket_number))

    def test_call_transfer_success_finite_depth(self):
        """
        Make a POST request to `resource` to begin transfering a resource.
        """
        self.url = reverse('resource_collection', kwargs={'target_name': 'zenodo'})
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': ZENODO_TEST_USER_TOKEN,
                        'HTTP_PRESQT_SOURCE_TOKEN': self.source_token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore',
                        'HTTP_PRESQT_KEYWORD_ACTION': 'enhance'}
        response = self.client.post(self.url, data={"source_target_name": "github",
                                                    "source_resource_id": self.resource_id},
                                    **self.headers)
        self.ticket_number = response.data['ticket_number']
        self.process_info_path = 'mediafiles/transfers/{}/process_info.json'.format(
            self.ticket_number)
        self.transfer_job = response.data['transfer_job']
        process_info = read_file(self.process_info_path, True)

        self.assertEqual(self.transfer_job, ('http://testserver{}'.format(reverse(
            'transfer_job', kwargs={'ticket_number': self.ticket_number}))))

        response = self.client.get(self.transfer_job, **self.headers)
        self.assertEqual(response.data['message'], 'Transfer is being processed on the server')

        # Wait until the spawned off process finishes in the background
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(self.process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass
        # Check that transfer was successful
        response = self.client.get(self.transfer_job, **self.headers)

        self.assertEqual(response.data['status_code'], '200')
        # Fixity errors because we're dealing with GitHub
        self.assertEqual(response.data['message'],
                         'Transfer successful but with fixity errors.')

        test_user_projects = requests.get('https://zenodo.org/api/deposit/depositions',
                                          params={'access_token': ZENODO_TEST_USER_TOKEN}).json()
        for project in test_user_projects:
            if project['title'] == 'ProjectTwelve':
                requests.delete(project['links']['self'], params={
                                'access_token': ZENODO_TEST_USER_TOKEN})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/transfers/{}'.format(self.ticket_number))

    def test_transfer_keyword_enhancement_enhance(self):
        """
        Test that the keywords are getting enhanced correctly during a transfer with keywords
        existing only on the target and not in the FTS Metadata.
        """
        github_project_id = "209372336"
        github_target_keywords = ["animals", "eggs", "water"]
        self.headers['HTTP_PRESQT_KEYWORD_ACTION'] = 'enhance'
        # TRANSFER RESOURCE TO OSF
        response = self.client.post(self.url, data={
            "source_target_name": "github", "source_resource_id": github_project_id}, **self.headers)

        self.ticket_number = response.data['ticket_number']
        self.process_info_path = 'mediafiles/transfers/{}/process_info.json'.format(
            self.ticket_number)
        self.transfer_job = response.data['transfer_job']
        process_info = read_file(self.process_info_path, True)

        self.assertEqual(self.transfer_job, ('http://testserver{}'.format(reverse(
            'transfer_job', kwargs={'ticket_number': self.ticket_number}))))

        response = self.client.get(self.transfer_job, **self.headers)
        self.assertEqual(response.data['message'], 'Transfer is being processed on the server')

        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(self.process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass
        self.assertNotEqual(process_info['status'], 'in_progress')

        # VALIDATE KEYWORD AND METADATA FILE IN GITHUB
        headers = {"Authorization": "token {}".format(GITHUB_TEST_USER_TOKEN),
                   "Accept": 'application/vnd.github.mercy-preview+json'}
        project_url = 'https://api.github.com/repositories/{}'.format(github_project_id)
        response = requests.get(project_url, headers=headers)
        self.assertGreater(len(response.json()['topics']), len(github_target_keywords))
        metadata_link = "https://raw.githubusercontent.com/presqt-test-user/PrivateProject/master/PRESQT_FTS_METADATA.json"
        response = requests.get(metadata_link, headers=headers)
        metadata_file = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(metadata_file['presqtKeywords']), 0)
        self.assertGreater(len(metadata_file['actions'][0]['keywords'].keys()), 0)
        self.assertEquals(metadata_file['actions'][0]['actionType'], "transfer_enhancement")

        # RESET KEYWORDS FROM GITHUB
        put_url = 'https://api.github.com/repos/presqt-test-user/PrivateProject/topics'
        data = {'names': github_target_keywords}
        response = requests.put(put_url, headers=headers, data=json.dumps(data))
        self.assertEqual(response.status_code, 200)

        # DELETE METADATA FILE IN GITHUB
        metadata_url = 'https://api.github.com/repos/presqt-test-user/PrivateProject/contents/PRESQT_FTS_METADATA.json?ref=master'
        # Make a GET request first to get the SHA which is needed to delete :eyeroll:
        get_response = requests.get(metadata_url, headers=headers)
        sha = get_response.json()['sha']
        delete_data = {
            "message": "Delete while testing",
            "committer": {
                "name": "PresQT",
                "email": "N/A"
            },
            "sha": sha
        }
        response = requests.delete(metadata_url, headers=headers, data=json.dumps(delete_data))
        self.assertEqual(response.status_code, 200)

        # VALIDATE KEYWORDS IN OSF
        # Get project ID
        osf_headers = {'HTTP_PRESQT_SOURCE_TOKEN': self.destination_token}
        osf_collection_response = self.client.get(self.url, **osf_headers)
        self.assertEqual(osf_collection_response.status_code, 200)
        osf_id = osf_collection_response.data[0]['id']
        # Get project details
        osf_detail_response = self.client.get(
            reverse('resource', kwargs={"target_name": "osf", "resource_id": osf_id}), **osf_headers)
        self.assertEqual(osf_detail_response.status_code, 200)
        self.assertGreater(len(osf_detail_response.data['extra']['tags']), 0)

        # VALIDATE METADATA FILE IN OSF
        headers = {'Authorization': 'Bearer {}'.format(OSF_UPLOAD_TEST_USER_TOKEN)}
        for node in requests.get('http://api.osf.io/v2/users/me/nodes', headers=headers).json()['data']:
            if node['attributes']['title'] == 'PrivateProject':
                storage_data = requests.get(
                    node['relationships']['files']['links']['related']['href'], headers=headers).json()
                folder_data = requests.get(
                    storage_data['data'][0]['relationships']['files']['links']['related']['href'], headers=headers).json()

        # Get the metadata file
        for data in folder_data['data']:
            if data['attributes']['name'] == 'PRESQT_FTS_METADATA.json':
                # Download the content of the metadata file
                metadata = requests.get(data['links']['move'], headers=headers).content
                break
        metadata = json.loads(metadata)

        self.assertGreater(len(metadata['presqtKeywords']), 0)
        self.assertGreater(len(metadata['actions'][0]['keywords'].keys()), 0)

        # DELETE TICKET FOLDER
        shutil.rmtree('mediafiles/transfers/{}'.format(self.ticket_number))

    def test_transfer_keyword_enhancement_enhance_existing_keywords(self):
        """
        Test that the keywords are getting enhanced correctly during a transfer with different
        keywords existing in the target and in the target resource's metadata file.
        """
        github_project_id = "209373575"
        github_target_keywords = ["airplane", "wood", "dirt"]
        github_metadata_keywords = ["cats", "dogs"]
        github_keywords = github_target_keywords + github_metadata_keywords
        self.headers['HTTP_PRESQT_KEYWORD_ACTION'] = 'enhance'

        # TRANSFER RESOURCE TO OSF
        response = self.client.post(self.url, data={
            "source_target_name": "github", "source_resource_id": github_project_id}, **self.headers)

        self.ticket_number = response.data['ticket_number']
        self.process_info_path = 'mediafiles/transfers/{}/process_info.json'.format(
            self.ticket_number)
        self.transfer_job = response.data['transfer_job']
        process_info = read_file(self.process_info_path, True)

        self.assertEqual(self.transfer_job, ('http://testserver{}'.format(reverse(
            'transfer_job', kwargs={'ticket_number': self.ticket_number}))))

        response = self.client.get(self.transfer_job, **self.headers)
        self.assertEqual(response.data['message'], 'Transfer is being processed on the server')

        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(self.process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass
        self.assertNotEqual(process_info['status'], 'in_progress')

        # VALIDATE KEYWORD AND METADATA FILE IN GITHUB
        headers = {"Authorization": "token {}".format(GITHUB_TEST_USER_TOKEN),
                   "Accept": 'application/vnd.github.mercy-preview+json'}
        project_url = 'https://api.github.com/repositories/{}'.format(github_project_id)
        response = requests.get(project_url, headers=headers)

        for keyword in github_keywords:
            self.assertIn(keyword, response.json()['topics'])

        # RESET KEYWORDS FROM GITHUB
        put_url = 'https://api.github.com/repos/presqt-test-user/ProjectFifteen/topics'
        data = {'names': github_target_keywords}
        response = requests.put(put_url, headers=headers, data=json.dumps(data))
        self.assertEqual(response.status_code, 200)

        # DELETE METADATA FILE IN GITHUB
        original_github_metadata = {
            "presqtKeywords": ["cats", "dogs"],
            "actions": []
        }
        updated_metadata_bytes = json.dumps(original_github_metadata, indent=4).encode('utf-8')
        updated_base64_metadata = base64.b64encode(updated_metadata_bytes).decode('utf-8')

        metadata_url = 'https://api.github.com/repos/presqt-test-user/ProjectFifteen/contents/PRESQT_FTS_METADATA.json?ref=master'
        # Make a GET request first to get the SHA which is needed to delete :eyeroll:
        get_response = requests.get(metadata_url, headers=headers)
        sha = get_response.json()['sha']
        data = {
            "message": "Reset Metadata",
            "committer": {
                "name": "PresQT",
                "email": "N/A"
            },
            "sha": sha,
            "content": updated_base64_metadata
        }
        response = requests.put(metadata_url, headers=headers, data=json.dumps(data))
        self.assertEqual(response.status_code, 200)

        # VALIDATE KEYWORDS IN OSF
        # Get project ID
        osf_headers = {'HTTP_PRESQT_SOURCE_TOKEN': self.destination_token}
        osf_collection_response = self.client.get(self.url, **osf_headers)
        self.assertEqual(osf_collection_response.status_code, 200)
        osf_id = osf_collection_response.data[0]['id']
        # Get project details
        osf_detail_response = self.client.get(
            reverse('resource', kwargs={"target_name": "osf", "resource_id": osf_id}), **osf_headers)
        self.assertEqual(osf_detail_response.status_code, 200)
        for keyword in github_keywords:
            self.assertIn(keyword, osf_detail_response.data['extra']['tags'])

        # VALIDATE METADATA FILE IN OSF
        headers = {'Authorization': 'Bearer {}'.format(OSF_UPLOAD_TEST_USER_TOKEN)}
        for node in requests.get('http://api.osf.io/v2/users/me/nodes', headers=headers).json()['data']:
            if node['attributes']['title'] == 'ProjectFifteen':
                storage_data = requests.get(
                    node['relationships']['files']['links']['related']['href'], headers=headers).json()
                folder_data = requests.get(
                    storage_data['data'][0]['relationships']['files']['links']['related']['href'], headers=headers).json()

        # Get the metadata file
        for data in folder_data['data']:
            if data['attributes']['name'] == 'PRESQT_FTS_METADATA.json':
                # Download the content of the metadata file
                metadata = requests.get(data['links']['move'], headers=headers).content
                break
        metadata = json.loads(metadata)

        for keyword in github_keywords:
            self.assertIn(keyword, metadata['presqtKeywords'])

        self.assertGreater(len(metadata['actions'][0]['keywords'].keys()), 0)

        # DELETE TICKET FOLDER
        shutil.rmtree('mediafiles/transfers/{}'.format(self.ticket_number))

    def test_transfer_keyword_enhancement_suggest(self):
        """
        Test that the keywords are getting suggested correctly during a transfer with keywords
        existing only on the target and not in the FTS Metadata.
        """
        github_project_id = "209372769"
        github_target_keywords = ["animals", "eggs", "water"]

        # TRANSFER RESOURCE TO OSF
        self.headers['HTTP_PRESQT_KEYWORD_ACTION'] = 'suggest'
        response = self.client.post(self.url, data={
            "source_target_name": "github", "source_resource_id": github_project_id}, **self.headers)

        self.ticket_number = response.data['ticket_number']
        self.process_info_path = 'mediafiles/transfers/{}/process_info.json'.format(
            self.ticket_number)
        self.transfer_job = response.data['transfer_job']
        process_info = read_file(self.process_info_path, True)

        self.assertEqual(self.transfer_job, ('http://testserver{}'.format(reverse(
            'transfer_job', kwargs={'ticket_number': self.ticket_number}))))

        response = self.client.get(self.transfer_job, **self.headers)
        self.assertEqual(response.data['message'], 'Transfer is being processed on the server')

        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(self.process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass
        self.assertNotEqual(process_info['status'], 'in_progress')

        response = self.client.get(self.transfer_job, **self.headers)
        self.assertEqual(response.data['initial_keywords'], github_target_keywords)
        self.assertGreater(len(response.data['enhanced_keywords']), 3)

        # VALIDATE KEYWORD AND VALIDATE THAT NO METADATA HAS BEEN WRITTEN TO GITHUB
        headers = {"Authorization": "token {}".format(GITHUB_TEST_USER_TOKEN),
                   "Accept": 'application/vnd.github.mercy-preview+json'}
        project_url = 'https://api.github.com/repositories/{}'.format(github_project_id)
        response = requests.get(project_url, headers=headers)
        self.assertEqual(response.json()['topics'], github_target_keywords)
        metadata_link = "https://raw.githubusercontent.com/presqt-test-user/ProjectTwentyEight/master/PRESQT_FTS_METADATA.json"
        response = requests.get(metadata_link, headers=headers)

        self.assertEqual(response.status_code, 404)

        # VALIDATE METADATA FILE IN OSF
        headers = {'Authorization': 'Bearer {}'.format(OSF_UPLOAD_TEST_USER_TOKEN)}
        for node in requests.get('http://api.osf.io/v2/users/me/nodes', headers=headers).json()['data']:
            if node['attributes']['title'] == 'ProjectTwentyEight':
                storage_data = requests.get(
                    node['relationships']['files']['links']['related']['href'], headers=headers).json()
                folder_data = requests.get(
                    storage_data['data'][0]['relationships']['files']['links']['related']['href'], headers=headers).json()

        # Get the metadata file
        for data in folder_data['data']:
            if data['attributes']['name'] == 'PRESQT_FTS_METADATA.json':
                # Download the content of the metadata file
                metadata = requests.get(data['links']['move'], headers=headers).content
                break
        metadata = json.loads(metadata)

        self.assertEqual(len(metadata['presqtKeywords']), 3)
        self.assertEqual(len(metadata['actions'][0]['keywords'].keys()), 0)

        # DELETE TICKET FOLDER
        shutil.rmtree('mediafiles/transfers/{}'.format(self.ticket_number))

    def test_get_error_400(self):
        """
        Return a 400 if the `presqt-destination-token` is missing in the headers.
        """
        response = self.client.post(self.url, data={"source_target_name": "github",
                                                    "source_resource_id": self.resource_id},
                                    **self.headers)
        ticket_number = response.data['ticket_number']
        process_info_path = 'mediafiles/transfers/{}/process_info.json'.format(ticket_number)
        process_info = read_file(process_info_path, True)

        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        url = reverse('transfer_job', kwargs={'ticket_number': ticket_number})
        headers = {'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        response = self.client.get(url, **headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'],
                         "PresQT Error: 'presqt-destination-token' missing in the request headers.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/transfers/{}'.format(ticket_number))

    def test_get_error_401(self):
        """
        Return a 401 if the 'presqt-destination-token' provided in the header does not match
        the 'presqt-destination-token' in the process_info file.
        """
        response = self.client.post(self.url, data={"source_target_name": "github",
                                                    "source_resource_id": self.resource_id},
                                    **self.headers)

        ticket_number = response.data['ticket_number']
        process_info_path = 'mediafiles/transfers/{}/process_info.json'.format(
            ticket_number)
        process_info = read_file(process_info_path, True)

        headers = {'HTTP_PRESQT_DESTINATION_TOKEN': 'EGGS',
                   'HTTP_PRESQT_SOURCE_TOKEN': self.source_token}
        response = self.client.get(response.data['transfer_job'], **headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['error'],
                         "PresQT Error: Header 'presqt-destination-token' does not match the 'presqt-destination-token' for this server process.")

        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        # Delete corresponding folder
        shutil.rmtree('mediafiles/transfers/{}'.format(ticket_number))

    def test_get_error_500_401_token_invalid(self):
        """
        Return a 500 if the BaseResource._transfer_resource method running on the server gets a 401 error because the token is invalid.
        """
        self.headers['HTTP_PRESQT_DESTINATION_TOKEN'] = 'bad_token'
        response = self.client.post(self.url, data={"source_target_name": "github",
                                                    "source_resource_id": self.resource_id},
                                    **self.headers)
        ticket_number = response.data['ticket_number']
        process_info_path = 'mediafiles/transfers/{}/process_info.json'.format(
            ticket_number)
        process_info = read_file(process_info_path, True)

        url = reverse('transfer_job', kwargs={'ticket_number': ticket_number})

        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        response = self.client.get(url, **self.headers)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "Token is invalid. Response returned a 401 status code.",
                          'status_code': 401})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/transfers/{}'.format(ticket_number))

    def test_get_error_500_500_server_error_upload(self):
        """
        Return a 500 if the BaseResource._transfer_resource function running on the server gets a
        500 error because the OSF server is down when attempting to transfer a project.
        """
        # Create a mock response class
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        # Mock the Session POST request to return a 500 server error when creating the project
        with patch('presqt.targets.osf.classes.base.OSFBase.post') as mock_request:
            mock_request.return_value = mock_req
            # Attempt to create the project (but the server is down from our mock!)
            response = self.client.post(self.url, data={"source_target_name": "github",
                                                        "source_resource_id": self.resource_id},
                                        **self.headers)
            ticket_number = response.data['ticket_number']
            process_info_path = 'mediafiles/transfers/{}/process_info.json'.format(
                ticket_number)
            process_info = read_file(process_info_path, True)

        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        # Check in on the transfer job and verify we got the 500 for the server error
        url = reverse('transfer_job', kwargs={'ticket_number': ticket_number})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "Response has status code 500 while creating project ProjectTwelve",
                          'status_code': 400})
        # Delete corresponding folder
        shutil.rmtree('mediafiles/transfers/{}'.format(ticket_number))

    def test_get_error_500_500_server_error_download(self):
        """
        Return a 500 if the BaseResource._transfer_resource function running on the server gets a
        500 error because the GitHub server is down when attempting to transfer a project.
        """
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        # Mock the Session POST request to return a 500 server error when creating the project
        with patch('presqt.targets.github.functions.download.github_download_resource') as mock_request:
            mock_request.return_value = mock_req
            # Attempt to create the project (but the server is down from our mock!)
            response = self.client.post(self.url, data={"source_target_name": "github",
                                                        "source_resource_id": "garbage_id"},
                                        **self.headers)
            ticket_number = response.data['ticket_number']
            process_info_path = 'mediafiles/transfers/{}/process_info.json'.format(
                ticket_number)
            process_info = read_file(process_info_path, True)

        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        # Check in on the transfer job and verify we got the 500 for the server error
        url = reverse('transfer_job', kwargs={'ticket_number': ticket_number})
        response = self.client.get(url, **self.headers)

        self.assertEqual(response.data,
                         {'message': "The resource with id, garbage_id, does not exist for this user.",
                          'status_code': 404})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/transfers/{}'.format(ticket_number))

    def test_transfer_invalid_requests(self):
        """
        Various invalidly formatted request tests.
        """
        # Bad Target Name #
        response = self.client.post(self.url, data={"source_target_name": "eggs",
                                                    "source_resource_id": self.resource_id},
                                    **self.headers)
        self.assertEqual(response.data['error'], "PresQT Error: 'eggs' is not a valid Target name.")

    def test_transfer_in_targets_not_allowed(self):
        """
        If a transfer target doesn't allow transfer from the source, an error message is displayed.
        """
        json_file = open('presqt/api_v1/tests/resources/transfer_targets_test.json')

        with patch("builtins.open") as mock_file:
            mock_file.return_value = json_file
            self.assertRaises(PresQTValidationError, transfer_target_validation, 'github', 'osf')

    def test_transfer_out_targets_not_allowed(self):
        """
        If a transfer target doesn't allow transfer to the source, an error message is displayed.
        """
        json_file = open('presqt/api_v1/tests/resources/transfer_targets_test.json')

        with patch("builtins.open") as mock_file:
            mock_file.return_value = json_file
            self.assertRaises(PresQTValidationError, transfer_target_validation, 'osf', 'github')

    def test_get_error_500_400_metadata_file(self):
        """
        Return a 400 if the user attempts to transfer the PRESQT_FTS_METADATA.json file
        """
        headers = {'HTTP_PRESQT_DESTINATION_TOKEN': GITHUB_TEST_USER_TOKEN,
                   'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN,
                   'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore',
                   'HTTP_PRESQT_KEYWORD_ACTION': 'enhance'}
        url = reverse('resource_collection', kwargs={'target_name': 'github'})

        response = self.client.post(url,
                                    data={"source_target_name": "osf",
                                          "source_resource_id": '5db34c37af84c3000ee1487d'},
                                    **headers)

        ticket_number = response.data['ticket_number']
        process_info_path = 'mediafiles/transfers/{}/process_info.json'.format(ticket_number)
        process_info = read_file(process_info_path, True)

        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        url = reverse('transfer_job', kwargs={'ticket_number': ticket_number})
        response = self.client.get(url, **headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "PresQT Error: PresQT FTS metadata cannot not be transferred by itself.",
                          'status_code': 400})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/transfers/{}'.format(ticket_number))

    def test_transfer_target_keyword_error(self):
        """
        This test exists to test the error raising works in target functions in enhance_keywords()
        """
        github_id = "209373160:__pycache__"
        self.headers['HTTP_PRESQT_KEYWORD_ACTION'] = 'enhance'

        # TRANSFER RESOURCE TO OSF
        response = self.client.post(self.url, data={
            "source_target_name": "github", "source_resource_id": github_id}, **self.headers)

        self.ticket_number = response.data['ticket_number']
        self.process_info_path = 'mediafiles/transfers/{}/process_info.json'.format(
            self.ticket_number)
        self.transfer_job = response.data['transfer_job']
        process_info = read_file(self.process_info_path, True)

        self.assertEqual(self.transfer_job, ('http://testserver{}'.format(reverse(
            'transfer_job', kwargs={'ticket_number': self.ticket_number}))))

        response = self.client.get(self.transfer_job, **self.headers)
        self.assertEqual(response.data['message'], 'Transfer is being processed on the server')

        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(self.process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass
        self.assertNotEqual(process_info['status'], 'in_progress')

        # DELETE TICKET FOLDER
        shutil.rmtree('mediafiles/transfers/{}'.format(self.ticket_number))

    def test_keyword_upload_raises_error_during_transfer(self):
        """
        Test that the transfer endpoint is catching an error returned from the target server
        when attempting to update metadata
        """
        self.headers['HTTP_PRESQT_KEYWORD_ACTION'] = 'enhance'

        # Create a mock response class
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        with patch('requests.put') as mock_request:
            mock_request.return_value = mock_req

            github_id = "209373160:__pycache__"

            # TRANSFER RESOURCE TO OSF
            response = self.client.post(self.url, data={
                "source_target_name": "github", "source_resource_id": github_id}, **self.headers)

            self.ticket_number = response.data['ticket_number']
            self.process_info_path = 'mediafiles/transfers/{}/process_info.json'.format(
                self.ticket_number)
            self.transfer_job = response.data['transfer_job']
            process_info = read_file(self.process_info_path, True)

            self.assertEqual(self.transfer_job, ('http://testserver{}'.format(reverse(
                'transfer_job', kwargs={'ticket_number': self.ticket_number}))))

            response = self.client.get(self.transfer_job, **self.headers)
            self.assertEqual(response.data['message'], 'Transfer is being processed on the server')

            while process_info['status'] == 'in_progress':
                try:
                    process_info = read_file(self.process_info_path, True)
                except json.decoder.JSONDecodeError:
                    # Pass while the process_info file is being written to
                    pass
            self.assertNotEqual(process_info['status'], 'in_progress')

            # DELETE TICKET FOLDER
            shutil.rmtree('mediafiles/transfers/{}'.format(self.ticket_number))

        with patch('requests.patch') as mock_request:
            mock_request.return_value = mock_req

            github_id = "209373160:__pycache__"

            # TRANSFER RESOURCE TO OSF
            response = self.client.post(self.url, data={
                "source_target_name": "github", "source_resource_id": github_id}, **self.headers)

            self.ticket_number = response.data['ticket_number']
            self.process_info_path = 'mediafiles/transfers/{}/process_info.json'.format(
                self.ticket_number)
            self.transfer_job = response.data['transfer_job']
            process_info = read_file(self.process_info_path, True)

            self.assertEqual(self.transfer_job, ('http://testserver{}'.format(reverse(
                'transfer_job', kwargs={'ticket_number': self.ticket_number}))))

            response = self.client.get(self.transfer_job, **self.headers)
            self.assertEqual(response.data['message'], 'Transfer is being processed on the server')

            while process_info['status'] == 'in_progress':
                try:
                    process_info = read_file(self.process_info_path, True)
                except json.decoder.JSONDecodeError:
                    # Pass while the process_info file is being written to
                    pass
            self.assertNotEqual(process_info['status'], 'in_progress')

            # DELETE TICKET FOLDER
            shutil.rmtree('mediafiles/transfers/{}'.format(self.ticket_number))


class TestTransferJobPATCH(SimpleTestCase):
    """
    Test the `api_v1/transfer/<ticket_id>/` endpoint's PATCH method.

    Testing only PresQT core code.
    """

    def setUp(self):
        self.client = APIClient()
        self.destination_token = OSF_UPLOAD_TEST_USER_TOKEN
        self.source_token = GITHUB_TEST_USER_TOKEN
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': self.destination_token,
                        'HTTP_PRESQT_SOURCE_TOKEN': self.source_token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore',
                        'HTTP_PRESQT_KEYWORD_ACTION': 'suggest'}
        self.resource_id = '209373660'
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})

    def test_success_200(self):
        """
        Return a 200 for successful cancelled transfer process.
        """
        transfer_response = self.client.post(self.url, data={
            "source_target_name": "github", "source_resource_id": self.resource_id}, **self.headers)

        ticket_number = transfer_response.data['ticket_number']
        ticket_path = 'mediafiles/transfers/{}'.format(ticket_number)
        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the spawned off process has a function_process_id to cancel the transfer
        while not process_info['function_process_id']:
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        transfer_patch_url = reverse('transfer_job', kwargs={'ticket_number': ticket_number})
        transfers_patch_url_response = self.client.patch(transfer_patch_url, **self.headers)

        self.assertEquals(transfers_patch_url_response.status_code, 200)
        self.assertEquals(
            transfers_patch_url_response.data['message'],
            'Transfer was cancelled by the user')

        process_info = read_file('{}/process_info.json'.format(ticket_path), True)

        self.assertEquals(process_info['message'], 'Transfer was cancelled by the user')
        self.assertEquals(process_info['status'], 'failed')
        self.assertEquals(process_info['status_code'], '499')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/transfers/{}'.format(ticket_number))

    def test_success_406(self):
        """
        Return a 406 for unsuccessful cancel because the transfer finished already.
        """
        transfer_response = self.client.post(self.url, data={
            "source_target_name": "github", "source_resource_id": self.resource_id}, **self.headers)
        ticket_number = transfer_response.data['ticket_number']
        ticket_path = 'mediafiles/transfers/{}'.format(ticket_number)
        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the spawned off process finishes to attempt to cancel transfer
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        transfer_patch_url = reverse('transfer_job', kwargs={'ticket_number': ticket_number})
        transfers_patch_url_response = self.client.patch(transfer_patch_url, **self.headers)

        self.assertEquals(transfers_patch_url_response.status_code, 406)
        self.assertEquals(transfers_patch_url_response.data['message'],
                          "Transfer successful. Fixity can't be determined because GitHub may not have provided a file checksum. See PRESQT_FTS_METADATA.json for more details.")

        process_info = read_file('{}/process_info.json'.format(ticket_path), True)

        self.assertEquals(process_info['message'],
                          "Transfer successful. Fixity can't be determined because GitHub may not have provided a file checksum. See PRESQT_FTS_METADATA.json for more details.")
        self.assertEquals(process_info['status'], 'finished')
        self.assertEquals(process_info['status_code'], '200')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/transfers/{}'.format(ticket_number))

    def test_get_error_400(self):
        """
        Return a 400 if the `presqt-destination-token` is missing in the headers.
        """
        response = self.client.post(self.url, data={"source_target_name": "github",
                                                    "source_resource_id": self.resource_id},
                                    **self.headers)
        ticket_number = response.data['ticket_number']

        url = reverse('transfer_job', kwargs={'ticket_number': ticket_number})
        headers = {'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        response = self.client.patch(url, **headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'],
                         "PresQT Error: 'presqt-destination-token' missing in the request headers.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/transfers/{}'.format(ticket_number))
