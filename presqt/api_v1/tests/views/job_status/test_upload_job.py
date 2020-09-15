import json
import shutil
from unittest.mock import patch

import requests
from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import OSF_UPLOAD_TEST_USER_TOKEN
from presqt.api_v1.utilities import hash_tokens
from presqt.utilities import read_file, write_file
from presqt.targets.osf.utilities import delete_users_projects


class TestUploadJobGET(SimpleTestCase):
    """
    Test the `api_v1/uploads/<ticket_id>/` endpoint's GET method.
    """

    def setUp(self):
        self.client = APIClient()
        self.token = OSF_UPLOAD_TEST_USER_TOKEN
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': self.token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore',
                        'HTTP_PRESQT_EMAIL_OPT_IN': ''}
        self.ticket_number = hash_tokens(OSF_UPLOAD_TEST_USER_TOKEN)

    def tearDown(self):
        """
        This should run at the end of this test class
        """
        delete_users_projects(self.token)

    def call_upload_resources(self):
        """
        Make a POST request to `resource` to begin uploading a resource
        """
        response = self.client.post(
            self.url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

        # Verify the status code
        self.assertEqual(response.status_code, 202)
        self.upload_job = response.data['upload_job']
        self.process_info_path = 'mediafiles/jobs/{}/process_info.json'.format(
            self.ticket_number)
        process_info = read_file(self.process_info_path, True)

        # Verify the upload_job link is what we expect
        self.assertEqual(self.upload_job, ('http://testserver{}'.format(reverse(
            'job_status', kwargs={'action': 'upload'}))))

        # Save initial process data that we can use to rewrite to the process_info file for testing
        self.initial_process_info = process_info

        # Wait until the spawned off process finishes in the background
        while process_info['resource_upload']['status'] == 'in_progress':
            try:
                process_info = read_file(self.process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        self.assertNotEqual(process_info['resource_upload']['status'], 'in_progress')

    @staticmethod
    def process_wait(process_info, ticket_path):
        # Wait until the spawned off process finishes in the background to do further validation
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

    def test_get_success_multiple_duplicate_projects_osf(self):
        """
        Return a 200 if the GET was successful and the resources were uploaded.
        Ensure proper naming conventions of duplicate projects
        """
        # First Project
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.call_upload_resources()

        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **self.headers)
        ticket_one = self.ticket_number
        # Verify the status code and data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Upload successful.')
        self.assertEqual(response.data['failed_fixity'], [])
        self.assertEqual(response.data['resources_ignored'], [])
        self.assertEqual(response.data['resources_updated'], [])

        # Second Project
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.call_upload_resources()

        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **self.headers)
        # Verify the status code and data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Upload successful.')

        # Third Project
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.call_upload_resources()

        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **self.headers)
        # Verify the status code and data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Upload successful.')

        response = requests.get('http://api.osf.io/v2/users/me/nodes',
                                headers={'Authorization': 'Bearer {}'.format(self.token)}).json()
        expected_titles = ['NewProject', 'NewProject (PresQT1)', 'NewProject (PresQT2)']
        titles = [node['attributes']['title'] for node in response['data']]

        self.assertEqual(sorted(expected_titles), sorted(titles))

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(ticket_one))

    def test_get_success_osf(self):
        """
        Return a 200 if the GET was successful and the resources were uploaded.
        """
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.call_upload_resources()

        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **self.headers)

        # Verify the status code and data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Upload successful.')
        self.assertEqual(response.data['failed_fixity'], [])
        self.assertEqual(response.data['resources_ignored'], [])
        self.assertEqual(response.data['resources_updated'], [])

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_success_202_osf(self):
        """
        Return a 202 if the GET was successful and the resource upload is in progress.
        """
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.call_upload_resources()

        # Update the fixity_info.json to say the resource hasn't finished processing
        write_file(self.process_info_path, self.initial_process_info, True)

        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **self.headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['message'], 'Saving files to server and validating bag...')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_error_400_osf(self):
        """
        Return a 400 if the `presqt-destination-token` is missing in the headers.
        """
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.call_upload_resources()

        url = reverse('job_status', kwargs={'action': 'upload'})
        headers = {'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore', 'HTTP_PRESQT_EMAIL_OPT_IN': ''}
        response = self.client.get(url, **headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'],
                         "PresQT Error: 'presqt-destination-token' missing in the request headers.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_error_404_osf(self):
        """
        Return a 404 if the ticket_number provided is not a valid ticket number.
        """
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.call_upload_resources()
        headers = {'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore',
                   'HTTP_PRESQT_DESTINATION_TOKEN': 'bad_ticket',
                   'HTTP_PRESQT_EMAIL_OPT_IN': ''}
        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], "PresQT Error: Invalid ticket number, '{}'.".format(
            hash_tokens('bad_ticket')))

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_error_500_401_token_invalid_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource method running on the server gets a 401 error because the token is invalid.
        """
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.headers['HTTP_PRESQT_DESTINATION_TOKEN'] = 'bad_token'
        self.ticket_number = hash_tokens('bad_token')
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.call_upload_resources()

        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **self.headers)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['message'],
                         "Token is invalid. Response returned a 401 status code.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_error_500_400_not_container_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource method running on the server gets a 401
        error because the resource_id provided is not a container
        """
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.call_upload_resources()

        headers = {'Authorization': 'Bearer {}'.format(OSF_UPLOAD_TEST_USER_TOKEN)}
        for node in requests.get('http://api.osf.io/v2/users/me/nodes', headers=headers).json()['data']:
            if node['attributes']['title'] == 'NewProject':
                storage_data = requests.get(
                    node['relationships']['files']['links']['related']['href'], headers=headers).json()
                folder_data = requests.get(
                    storage_data['data'][0]['relationships']['files']['links']['related']['href'], headers=headers).json()
                file_data = requests.get(
                    folder_data['data'][0]['relationships']['files']['links']['related']['href'], headers=headers).json()
                break

        ticket_number = self.ticket_number
        # Attempt to make a new request to the file resource
        file_id = file_data['data'][0]['id']
        self.url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': file_id})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.call_upload_resources()

        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **self.headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['message'],
                         "The Resource provided, {}, is not a container".format(file_id))

        # Delete corresponding folders
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_error_500_403_unauthorized_resource_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource function running on the server gets a 403 error because the resource is not available with the given token.
        """
        self.url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'q5xmw'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.call_upload_resources()

        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **self.headers)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data['message'], "User does not have access to this resource with the token provided.")

        # Delete corresponding folders
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_error_500_404_resource_not_found_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource function running on the server gets a 404 error because the resource requested does not exist.
        """
        self.url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'bad_id'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.call_upload_resources()

        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **self.headers)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['message'],


                         "Resource with id 'bad_id' not found for this user.")

        # Delete corresponding folders
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_error_500_410_gone_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource function running on the server gets a 410 error because the resource requested no longer exists.
        """
        self.url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'k453b'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.call_upload_resources()

        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **self.headers)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['message'],
                         "The requested resource is no longer available.")

        # Delete corresponding folders
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_error_500_500_server_error_create_project_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource function running on the server gets a
        500 error because the OSF server is down when attempting to create a project.
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
            self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
            self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
            self.call_upload_resources()

        # Check in on the upload job and verify we got the 500 for the server error
        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['message'],
                         "Response has status code 500 while creating project NewProject")

        # Delete corresponding folders
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_error_500_500_server_error_create_folder_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource function running on the server gets a
        500 error because the OSF server is down when attempting to create a folder
        """
        # Create a mock response class
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        # Mock the Session POST request to return a 500 server error when creating the folder
        with patch('presqt.targets.osf.classes.base.OSFBase.put') as mock_request:
            mock_request.return_value = mock_req
            # Attempt to create the folder (but the server is down from our mock!)
            self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
            self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
            self.call_upload_resources()

        # Check in on the upload job and verify we got the 500 for the server error
        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data['message'], "Response has status code 500 while creating folder funnyfunnyimages")

        # Delete corresponding folders
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_error_500_500_server_error_create_file_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource function running on the server gets a
        500 error because the OSF server is down when attempting to create a file.
        """

        # Create a mock response class
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        # Mock the Session POST request to return a 500 server error when creating the file
        with patch('presqt.targets.osf.classes.base.OSFBase.put') as mock_request:
            mock_request.return_value = mock_req
            # Attempt to create the project (but the server is down from our mock!)
            self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
            self.file = 'presqt/api_v1/tests/resources/upload/ProjectSingleFileToUpload.zip'
            self.call_upload_resources()

            # Check in on the upload job and verify we got the 500 for the server error
            url = reverse('job_status', kwargs={'action': 'upload'})
            response = self.client.get(url, **self.headers)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(
                response.data['message'], "Response has status code 500 while creating file Screen Shot 2019-07-15 at 3.51.13 PM.png")

            # Delete corresponding folders
            shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_error_500_500_server_error_create_file_duplicate_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource function running on the server gets a
        500 error because the OSF server is down when attempting to create a duplicate file.
        """
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = 'update'

        # Create a mock response class
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        # Create a project with a single file in it. We will then attempt to upload that file again.
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectSingleFileToUpload.zip'
        self.call_upload_resources()

        # Delete corresponding folders
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

        # Get the project id so we can attempt to upload the file to it.
        headers = {'Authorization': 'Bearer {}'.format(OSF_UPLOAD_TEST_USER_TOKEN)}
        for node in requests.get('http://api.osf.io/v2/users/me/nodes', headers=headers).json()[
                'data']:
            if node['attributes']['title'] == 'NewProject':
                node_id = node['id']
                break

        # Mock the Session POST request to return a 500 server error when creating the file
        with patch('presqt.targets.osf.classes.file.File.update') as mock_request:
            mock_request.return_value = mock_req
            # Attempt to create the project (but the server is down from our mock!)
            self.url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': node_id})
            self.file = 'presqt/api_v1/tests/resources/upload/ProjectSingleDuplicateFileToUpload.zip'
            self.call_upload_resources()

        # Check in on the upload job and verify we got the 500 for the server error
        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data['message'], "Response has status code 500 while updating file Screen Shot 2019-07-15 at 3.51.13 PM.png")

        # Delete corresponding folders
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_error_500_400_bad_project_format_multiple_folders_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource function running on the server gets a
        401 error because a bad project format given with there being multiple top level folders.
        """
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/BadProjectMultipleFolders.zip'
        self.call_upload_resources()

        # Check in on the upload job and verify we got the 500 for the server error
        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data['message'], "PresQT Error: Repository is not formatted correctly. Multiple directories exist at the top level.")

        # Delete corresponding folders
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_error_500_400_bad_project_format_file_exists_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource function running on the server gets a
        401 error because a bad project format given with there a file at the top level.
        """
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/SingleFileDuplicate.zip'
        self.call_upload_resources()

        # Check in on the upload job and verify we got the 500 for the server error
        url = reverse('job_status', kwargs={'action': 'upload'})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data['message'], "PresQT Error: Repository is not formatted correctly. Files exist at the top level.")

        # Delete corresponding folders
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_error_500_400_not_a_bag_zip_file_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource function running on the server gets a
        400 error because a zip other than a bag is provided in the request.
        """
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/not_a_bag.zip'
        response = self.client.post(
            self.url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

        # Verify the status code
        self.assertEqual(response.status_code, 400)


class TestUploadJobPATCH(SimpleTestCase):
    """
    Test the `api_v1/upload/<ticket_id>/` endpoint's PATCH method.
    """

    def setUp(self):
        self.client = APIClient()
        self.token = OSF_UPLOAD_TEST_USER_TOKEN
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': self.token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore',
                        'HTTP_PRESQT_EMAIL_OPT_IN': ''}
        self.upload_url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.ticket_number = hash_tokens(self.token)

    def test_success_200(self):
        """
        Return a 200 for successful cancelled upload process.
        """
        self.client.post(self.upload_url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

        ticket_path = 'mediafiles/jobs/{}'.format(self.ticket_number)
        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['resource_upload']['status'], 'in_progress')

        # Wait until the spawned off process has a function_process_id to cancel the upload
        while not process_info['resource_upload']['function_process_id']:
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_patch_url = reverse('job_status', kwargs={'action': 'upload'})
        upload_patch_url_response = self.client.patch(upload_patch_url, **self.headers)

        self.assertEquals(upload_patch_url_response.status_code, 200)
        self.assertEquals(
            upload_patch_url_response.data['message'],
            'Upload was cancelled by the user')

        process_info = read_file('{}/process_info.json'.format(ticket_path), True)

        self.assertEquals(process_info['resource_upload']['message'],
                          'Upload was cancelled by the user')
        self.assertEquals(process_info['resource_upload']['status'], 'failed')
        self.assertEquals(process_info['resource_upload']['status_code'], '499')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_success_406(self):
        """
        Return a 406 for unsuccessful cancel because the upload finished already.
        """
        self.client.post(self.upload_url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

        ticket_path = 'mediafiles/jobs/{}'.format(self.ticket_number)
        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['resource_upload']['status'], 'in_progress')

        # Wait until the spawned off process has a function_process_id to cancel the upload
        while process_info['resource_upload']['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_patch_url = reverse('job_status', kwargs={'action': 'upload'})
        upload_patch_url_response = self.client.patch(upload_patch_url, **self.headers)

        self.assertEquals(upload_patch_url_response.status_code, 406)
        self.assertEquals(upload_patch_url_response.data['message'], 'Upload successful.')

        process_info = read_file('{}/process_info.json'.format(ticket_path), True)

        self.assertEquals(process_info['resource_upload']['message'], 'Upload successful.')
        self.assertEquals(process_info['resource_upload']['status'], 'finished')
        self.assertEquals(process_info['resource_upload']['status_code'], '200')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_get_error_400_osf(self):
        """
        Return a 400 if the `presqt-destination-token` is missing in the headers.
        """
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.client.post(self.upload_url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

        ticket_path = 'mediafiles/jobs/{}'.format(self.ticket_number)
        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['resource_upload']['status'], 'in_progress')

        # Wait until the spawned off process has a function_process_id to cancel the upload
        while process_info['resource_upload']['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        url = reverse('job_status', kwargs={'action': 'upload'})
        headers = {'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        response = self.client.patch(url, **headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'],
                         "PresQT Error: 'presqt-destination-token' missing in the request headers.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))
