import io
import json
import requests
import shutil
from unittest.mock import patch, MagicMock
import zipfile

from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import (OSF_UPLOAD_TEST_USER_TOKEN, GITHUB_TEST_USER_TOKEN,
                                  ZENODO_TEST_USER_TOKEN, OSF_TEST_USER_TOKEN)

from presqt.api_v1.utilities import transfer_target_validation
from presqt.api_v1.views.resource.base_resource import BaseResource
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
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
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
        self.assertEqual(response.data['message'], 'Transfer successful but with fixity errors.')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/transfers/{}'.format(self.ticket_number))

    def test_call_transfer_success_finite_depth(self):
        """
        Make a POST request to `resource` to begin transfering a resource.
        """
        self.url = reverse('resource_collection', kwargs={'target_name': 'zenodo'})
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': ZENODO_TEST_USER_TOKEN,
                        'HTTP_PRESQT_SOURCE_TOKEN': self.source_token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
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
        self.assertEqual(response.data['message'], 'Transfer successful but with fixity errors.')

        test_user_projects = requests.get('https://zenodo.org/api/deposit/depositions',
                                          params={'access_token': ZENODO_TEST_USER_TOKEN}).json()
        for project in test_user_projects:
            if project['title'] == 'ProjectTwelve':
                requests.delete(project['links']['self'], params={
                                'access_token': ZENODO_TEST_USER_TOKEN})

        # Delete corresponding folder
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
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
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
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
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
                          'Transfer successful but with fixity errors.')

        process_info = read_file('{}/process_info.json'.format(ticket_path), True)

        self.assertEquals(process_info['message'], 'Transfer successful but with fixity errors.')
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