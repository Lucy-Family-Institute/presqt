import multiprocessing
import os
import shutil
from unittest.mock import patch

from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import OSF_TEST_USER_TOKEN, OSF_UPLOAD_TEST_USER_TOKEN
from presqt.targets.utilities import process_wait
from presqt.utilities import read_file
from presqt.api_v1.views.resource.base_resource import BaseResource
from presqt.targets.osf.utilities import delete_users_projects


class TestResourceGET(TestCase):
    """
    Test the endpoint's GET method for
    `api_v1/targets/{target_name}/resources/{resource_id}.{resource_format}/`

    Testing only PresQT Core code.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN}

    def test_400_bad_resource_format(self):
        """
        Return a 404 if the GET method is unsuccessful because the path parameter resource_format
        is not valid.
        """
        resource_id = 'cmn5z'
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id,
                                          'resource_format': 'bad_format'})
        response = self.client.get(url, **self.header)
        # Verify the Status Code and data
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {"error": "bad_format is not a valid format for this endpoint."})

    def test_error_400_missing_token(self):
        """
        Return a 400 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': '3',
                                          'resource_format': 'json'})
        response = self.client.get(url)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "'presqt-source-token' missing in the request headers."})

    def test_error_400_target_not_supported_test_target(self):
        """
        Return a 400 if the GET method fails because the target requested does not support
        this endpoint's action.
        """
        with open('presqt/api_v1/tests/resources/targets_test.json') as json_file:
            with patch("builtins.open") as mock_file:
                mock_file.return_value = json_file
                url = reverse('resource', kwargs={'target_name': 'test',
                                                  'resource_id': 'cmn5z',
                                                  'resource_format': 'json'})
                response = self.client.get(url, **self.header)
                # Verify the error status code and message
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.data,
                    {'error': "'test' does not support the action 'resource_detail'."})

    def test_error_404_bad_target_name(self):
        """
        Return a 404 if the GET method fails because a bad target_name was given.
        """
        url = reverse('resource', kwargs={'target_name': 'bad_name',
                                          'resource_id': '3',
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {'error': "'bad_name' is not a valid Target name."})


class TestResourceGETZip(TestCase):
    """
    Test the `api_v1/targets/{target_name}/resources/{resource_id}.zip/` endpoint's GET method.

    Testing only PresQT Core code.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN}

    def test_error_400_target_not_supported_test_target(self):
        """
        Return a 400 if the GET method fails because the target requested does not support
        this endpoint's action.
        """
        with open('presqt/api_v1/tests/resources/targets_test.json') as json_file:
            with patch("builtins.open") as mock_file:
                mock_file.return_value = json_file
                url = reverse(
                    'resource', kwargs={'target_name': 'test',
                                        'resource_id': '5cd98510f244ec001fe5632f',
                                        'resource_format': 'zip'})
                response = self.client.get(url, **self.header)
                # Verify the error status code and message
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.data,
                    {'error': "'test' does not support the action 'resource_download'."})

    def test_error_404_bad_target_name(self):
        """
        Return a 404 if the GET method fails because a bad target_name was given.
        """
        url = reverse('resource', kwargs={'target_name': 'bad_name',
                                          'resource_id': '3',
                                          'resource_format': 'zip'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {'error': "'bad_name' is not a valid Target name."})

    def test_error_400_missing_token(self):
        """
        Return a 400 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': '3',
                                          'resource_format': 'zip'})
        response = self.client.get(url)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "'presqt-source-token' missing in the request headers."})


class TestResourcePOST(TestCase):
    """
    Test the endpoint's POST method for resource uploads:
         `api_v1/targets/{target_name}/resources/{resource_id}/`
         `api_v1/targets/{target_name}/resources/`

    Testing only PresQT Core code.
    """

    def setUp(self):
        self.client = APIClient()
        self.token = OSF_UPLOAD_TEST_USER_TOKEN
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': self.token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        self.good_zip_file = 'presqt/api_v1/tests/resources/upload/GoodBagIt.zip'

    def tearDown(self):
        """
        This should run at the end of this test class
        """
        delete_users_projects(self.token)

    def test_success_202_upload_fixity_failed(self):
        """
        Get a 202 if POST succeeds but with fixity errors.

        First we will run the upload endpoint to get a ticket number. We will then use that ticket
        number to make a fake bad hash dictionary that will get patched into a manual run of the
        upload function.
        """
        good_file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})

        # Hit the endpoint initially
        response = self.client.post(url, {'presqt-file': open(good_file, 'rb')}, **self.headers)
        self.assertEqual(response.status_code, 202)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)
        process_info_path = 'mediafiles/uploads/{}/process_info.json'.format(ticket_number)
        process_info = read_file(process_info_path, True)
        resource_main_dir = '{}/{}'.format(ticket_path, next(os.walk(ticket_path))[1][0])
        process_state = multiprocessing.Value('b', 0)

        # Wait for the process to finish
        process_wait(process_info, ticket_path)

        # Create bad hashes with the ticket number and run the upload function manually
        file_hashes = {'mediafiles/uploads/{}/BagItToUpload/data/NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png'.format(
            ticket_number): '6d33275234b28d77348e4e1049f58b95a485a7a441684a9eb9175d01c7f141ea'}
        with patch('presqt.targets.osf.classes.storage_folder.ContainerMixin.create_directory') as fake_send:
            fake_send.return_value = {'mediafiles/uploads/{}/BagItToUpload/data/NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png'.format(
                ticket_number): {'sha256': 'bad_hash', 'md5': 'another_bad_hash'}}, [], []

            BaseResource._upload_resource(resource_main_dir, process_info_path,
                                          'osf', 'resource_upload', OSF_UPLOAD_TEST_USER_TOKEN, None,
                                          process_state, 'sha256', file_hashes, 'ignore',
                                          process_info)

            process_info = read_file(process_info_path, True)
            self.assertEqual(process_info['message'], 'Upload successful but fixity failed.')
            self.assertEqual(process_info['failed_fixity'], [
                             'data/NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png'])

            # Delete corresponding folder
            shutil.rmtree('mediafiles/uploads/{}'.format(ticket_number))

    def test_error_400_target_not_supported_test_target(self):
        """
        Return a 400 if the POST method fails because the target requested does not supported
        this endpoint's action
        """
        file = open('presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip', 'rb')

        with open('presqt/api_v1/tests/resources/targets_test.json') as json_file:
            with patch("builtins.open") as mock_file:
                mock_file.return_value = json_file
                url = reverse('resource', kwargs={'target_name': 'test','resource_id': 'resource_id'})
                response = self.client.post(url, {'presqt-file': file}, **self.headers)
                # Verify the error status code and message
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.data, {'error': "'test' does not support the action 'resource_upload'."})

    def test_error_400_missing_token(self):
        """
        Return a 400 if the POST method fails because the presqt-destination-token was not provided.
        """
        headers = {'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'resource_id'})
        response = self.client.post(url, {'presqt-file': open('presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip', 'rb')}, **headers)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': "'presqt-destination-token' missing in the request headers."})

    def test_error_400_presqt_file_missing(self):
        """
        Return a 400 if the POST method fails because presqt-file was not provided in the request.
        """
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'resource_id'})
        response = self.client.post(url, **self.headers)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': "The file, 'presqt-file', is not found in the body of the request."})

    def test_error_400_not_zip_file(self):
        """
        Return a 400 if POST fails because the file provided in he request is not in zip format
        """
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'resource_id'})
        response = self.client.post(url, {'presqt-file': open('presqt/api_v1/tests/resources/targets_test.json', 'rb')}, **self.headers)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': "The file provided, 'presqt-file', is not a zip file."})

    def test_error_400_duplicate_action_missing(self):
        """
        Return a 400 if the POST fails because "'presqt-file-duplicate-action' missing in headers.
        """
        headers = {'HTTP_PRESQT_DESTINATION_TOKEN': OSF_UPLOAD_TEST_USER_TOKEN}
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'resource_id'})
        response = self.client.post(url, {'presqt-file': open('presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip', 'rb')}, **headers)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "'presqt-file-duplicate-action' missing in the request headers."})

    def test_error_400_invalid_action(self):
        """
        Return a 400 if the POST fails because an invalid 'file_duplicate_action' header was given.
        """
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = 'bad_action'
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'resource_id'})
        response = self.client.post(url, {
            'presqt-file': open('presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip', 'rb')}, **self.headers)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,{'error': "'bad_action' is not a valid file_duplicate_action. The options are 'ignore' or 'update'."})

    def test_error_400_bagit_manifest_error(self):
        """
        Return a 400 if the POST fails because the BagIt manifest doesn't match the bag provided because the manifest hashes don't match the current files' hashes.
        """
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': '5cd9895b840cae001a708c31'})
        response = self.client.post(url, {'presqt-file': open('presqt/api_v1/tests/resources/upload/BadBagItManifest.zip','rb')}, **self.headers)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': "Checksums failed to validate."})

    def test_error_400_bagit_missing_file(self):
        """
        Return a 400 if the POST fails because the BagIt manifest doesn't match the bag provided because a file is missing in the data.
        """
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': '5cd9895b840cae001a708c31'})
        response = self.client.post(url, {'presqt-file': open('presqt/api_v1/tests/resources/upload/BadBagItMissingFile.zip','rb')}, **self.headers)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': "Payload-Oxum validation failed. Expected 2 files and 283274 bytes but found 1 files and 87111 bytes"})

    def test_error_400_bagit_unknown_file(self):
        """
        Return a 400 if the POST fails because the BagIt manifest doesn't match the bag provided because there's an unexpected file in the data.
        """
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': '5cd9895b840cae001a708c31'})
        response = self.client.post(url, {'presqt-file': open('presqt/api_v1/tests/resources/upload/BadBagItUnknownFile.zip','rb')}, **self.headers)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': "data/fixity_info.json exists in manifest but was not found on filesystem"})
