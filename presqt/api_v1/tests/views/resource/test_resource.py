import multiprocessing
import os
import shutil
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import (OSF_TEST_USER_TOKEN, OSF_UPLOAD_TEST_USER_TOKEN,
                                  CURATE_ND_TEST_TOKEN)
from presqt.targets.utilities import process_wait
from presqt.utilities import read_file
from presqt.api_v1.utilities import hash_tokens
from presqt.api_v1.views.resource.base_resource import BaseResource
from presqt.targets.osf.utilities import delete_users_projects


class TestResourceGET(SimpleTestCase):
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
                         {"error": "PresQT Error: bad_format is not a valid format for this endpoint."})

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
                         {'error': "PresQT Error: 'presqt-source-token' missing in the request headers."})

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
                    {'error': "PresQT Error: 'test' does not support the action 'resource_detail'."})

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
        self.assertEqual(
            response.data, {'error': "PresQT Error: 'bad_name' is not a valid Target name."})


class TestResourceGETZip(SimpleTestCase):
    """
    Test the `api_v1/targets/{target_name}/resources/{resource_id}.zip/` endpoint's GET method.

    Testing only PresQT Core code.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN,
                       'HTTP_PRESQT_EMAIL_OPT_IN': ''}

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
                    {'error': "PresQT Error: 'test' does not support the action 'resource_download'."})

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
        self.assertEqual(
            response.data, {'error': "PresQT Error: 'bad_name' is not a valid Target name."})

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
                         {'error': "PresQT Error: 'presqt-source-token' missing in the request headers."})


class TestResourcePOSTWithFile(SimpleTestCase):
    """
    Test the endpoint's POST method for resource uploads when providing a file:
         `api_v1/targets/{target_name}/resources/{resource_id}/`
         `api_v1/targets/{target_name}/resources/`

    Testing only PresQT Core code.
    """

    def setUp(self):
        self.client = APIClient()
        self.token = OSF_UPLOAD_TEST_USER_TOKEN
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': self.token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore',
                        'HTTP_PRESQT_EMAIL_OPT_IN': ''}
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

        ticket_path = 'mediafiles/jobs/{}'.format(hash_tokens(self.token))
        process_info_path = 'mediafiles/jobs/{}/process_info.json'.format(hash_tokens(self.token))
        process_info = read_file(process_info_path, True)
        resource_main_dir = '{}/{}'.format(ticket_path, next(os.walk(ticket_path))[1][0])

        # Wait for the process to finish
        process_wait(process_info, ticket_path)

        # Create bad hashes with the ticket number and run the upload function manually
        file_hashes = {'mediafiles/jobs/{}/BagItToUpload/data/NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png'.format(
            hash_tokens(self.token)): '6d33275234b28d77348e4e1049f58b95a485a7a441684a9eb9175d01c7f141e'}

        # Create an instance of the BaseResource and add all of the appropriate class attributes
        # needed for _upload_resource()
        resource_instance = BaseResource()
        resource_instance.resource_main_dir = resource_main_dir
        resource_instance.ticket_number = hash_tokens(self.token)
        resource_instance.process_info_path = process_info_path
        resource_instance.destination_target_name = 'osf'
        resource_instance.action = 'resource_upload'
        resource_instance.destination_token = OSF_UPLOAD_TEST_USER_TOKEN
        resource_instance.hash_algorithm = 'sha256'
        resource_instance.file_hashes = file_hashes
        resource_instance.file_duplicate_action = 'ignore'
        resource_instance.destination_resource_id = None
        resource_instance.infinite_depth = True
        resource_instance.process_info_obj = {
            'presqt-destination-token': hash_tokens(self.token),
            'status': 'in_progress',
            'expiration': str('2012-04-28'),
            'message': 'Saving files to server and validating bag...',
            'status_code': None,
            'function_process_id': None,
            'upload_total_files': 0,
            'upload_files_finished': 0}
        resource_instance.source_fts_metadata_actions = []
        resource_instance.function_process = multiprocessing.Process()
        resource_instance.all_keywords = []
        resource_instance._upload_resource()

        process_info = read_file(process_info_path, True)
        self.assertEqual(process_info['resource_upload']['message'],
                         'Upload successful but with fixity errors.')
        self.assertEqual(process_info['resource_upload']['failed_fixity'], [
                         '/NewProject/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png'])

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(hash_tokens(self.token)))

    def test_error_400_target_not_supported_test_target(self):
        """
        Return a 400 if the POST method fails because the target requested does not supported
        this endpoint's action
        """
        file = open('presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip', 'rb')

        with open('presqt/api_v1/tests/resources/targets_test.json') as json_file:
            with patch("builtins.open") as mock_file:
                mock_file.return_value = json_file
                url = reverse('resource', kwargs={
                              'target_name': 'test', 'resource_id': 'resource_id'})
                response = self.client.post(url, {'presqt-file': file}, **self.headers)
                # Verify the error status code and message
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.data, {'error': "PresQT Error: 'test' does not support the action 'resource_upload'."})

    def test_error_400_missing_token(self):
        """
        Return a 400 if the POST method fails because the presqt-destination-token was not provided.
        """
        headers = {'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore', 'HTTP_PRESQT_EMAIL_OPT_IN': ''}
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'resource_id'})
        response = self.client.post(
            url, {'presqt-file': open('presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip', 'rb')}, **headers)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {'error': "PresQT Error: 'presqt-destination-token' missing in the request headers."})

    def test_error_400_presqt_file_missing(self):
        """
        Return a 400 if the POST method fails because presqt-file was not provided in the request.
        """
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'resource_id'})
        response = self.client.post(
            url, {'wrong-file-name': open('presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip', 'rb')}, **self.headers)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {'error': "PresQT Error: The file, 'presqt-file', is not found in the body of the request."})

    def test_error_400_not_zip_file(self):
        """
        Return a 400 if POST fails because the file provided in he request is not in zip format
        """
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'resource_id'})
        response = self.client.post(
            url, {'presqt-file': open('presqt/api_v1/tests/resources/targets_test.json', 'rb')}, **self.headers)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {'error': "PresQT Error: The file provided, 'presqt-file', is not a zip file."})

    def test_error_400_duplicate_action_missing(self):
        """
        Return a 400 if the POST fails because "'presqt-file-duplicate-action' missing in headers.
        """
        headers = {'HTTP_PRESQT_DESTINATION_TOKEN': OSF_UPLOAD_TEST_USER_TOKEN, 'HTTP_PRESQT_EMAIL_OPT_IN': ''}
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'resource_id'})
        response = self.client.post(
            url, {'presqt-file': open('presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip', 'rb')}, **headers)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "PresQT Error: 'presqt-file-duplicate-action' missing in the request headers."})

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
        self.assertEqual(response.data, {
                         'error': "PresQT Error: 'bad_action' is not a valid file_duplicate_action. The options are 'ignore' or 'update'."})

    def test_error_400_bagit_manifest_error(self):
        """
        Return a 400 if the POST fails because the BagIt manifest doesn't match the bag provided because the manifest hashes don't match the current files' hashes.
        """
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': '5cd9895b840cae001a708c31'})
        response = self.client.post(
            url, {'presqt-file': open('presqt/api_v1/tests/resources/upload/BadBagItManifest.zip', 'rb')}, **self.headers)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': "PresQT Error: Checksums failed to validate."})

    def test_error_400_bagit_missing_file(self):
        """
        Return a 400 if the POST fails because the BagIt manifest doesn't match the bag provided because a file is missing in the data.
        """
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': '5cd9895b840cae001a708c31'})
        response = self.client.post(
            url, {'presqt-file': open('presqt/api_v1/tests/resources/upload/BadBagItMissingFile.zip', 'rb')}, **self.headers)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
                         'error': "PresQT Error: Payload-Oxum validation failed. Expected 2 files and 283274 bytes but found 1 files and 87111 bytes"})

    def test_error_400_bagit_unknown_file(self):
        """
        Return a 400 if the POST fails because the BagIt manifest doesn't match the bag provided because there's an unexpected file in the data.
        """
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': '5cd9895b840cae001a708c31'})
        response = self.client.post(
            url, {'presqt-file': open('presqt/api_v1/tests/resources/upload/BadBagItUnknownFile.zip', 'rb')}, **self.headers)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
                         'error': "PresQT Error: data/fixity_info.json exists in manifest but was not found on filesystem"})


class TestResourcePOSTWithBody(SimpleTestCase):
    """
    Test the endpoint's POST method for resource uploads when providing source target to get it from
         `api_v1/targets/{target_name}/resources/{resource_id}/`
         `api_v1/targets/{target_name}/resources/`

    Testing only PresQT Core code.
    """

    def setUp(self):
        self.client = APIClient()
        self.source_token = CURATE_ND_TEST_TOKEN
        self.destination_token = OSF_UPLOAD_TEST_USER_TOKEN
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': self.destination_token,
                        'HTTP_PRESQT_SOURCE_TOKEN': self.source_token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore',
                        'HTTP_PRESQT_KEYWORD_ACTION': 'automatic',
                        'HTTP_PRESQT_EMAIL_OPT_IN': ''}

    def test_error_400_missing_destination_token(self):
        """
        Return a 400 if the POST method fails because the presqt-destination-token was not provided.
        """
        headers = self.headers
        headers.pop('HTTP_PRESQT_DESTINATION_TOKEN')
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.post(url, {
            "source_target_name": "curate_nd",
            "source_resource_id": "dj52w379504",
            "keywords": []}, **headers, format='json')
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "PresQT Error: 'presqt-destination-token' missing in the request headers."})

    def test_error_400_missing_source_token(self):
        """
        Return a 400 if the POST method fails because the presqt-destination-token was not provided.
        """
        headers = self.headers
        headers.pop('HTTP_PRESQT_SOURCE_TOKEN')
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.post(url, {
            "source_target_name": "curate_nd",
            "source_resource_id": "dj52w379504",
            "keywords": []}, **headers, format='json')
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "PresQT Error: 'presqt-source-token' missing in the request headers."})

    def test_error_400_duplicate_action_missing(self):
        """
        Return a 400 if the POST fails because "'presqt-file-duplicate-action' missing in headers.
        """
        headers = self.headers
        headers.pop('HTTP_PRESQT_FILE_DUPLICATE_ACTION')
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.post(url, {
            "source_target_name": "curate_nd",
            "source_resource_id": "dj52w379504",
            "keywords": []}, **headers, format='json')
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "PresQT Error: 'presqt-file-duplicate-action' missing in the request headers."})

    def test_error_400_invalid_action(self):
        """
        Return a 400 if the POST fails because an invalid 'file_duplicate_action' header was given.
        """
        headers = self.headers
        headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = 'bad_action'
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.post(url, {
            "source_target_name": "curate_nd",
            "source_resource_id": "dj52w379504",
            "keywords": []}, **headers, format='json')
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'error': "PresQT Error: 'bad_action' is not a valid file_duplicate_action. The options are 'ignore' or 'update'."})

    def test_error_400_source_target_name_missing(self):
        """
        Return a 400 if the POST fails because the source_target_name is missing from the request body.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.post(url, {
            "source_resource_id": "dj52w379504",
            "keywords": []}, **self.headers, format='json')
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {'error': "PresQT Error: source_target_name was not found in the request body."})

    def test_error_400_source_resource_id_missing(self):
        """
        Return a 400 if the POST fails because the source_resource_id is missing from the request body.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.post(url, {
            "source_target_name": "curate_nd",
            "keywords": []}, **self.headers, format='json')
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "PresQT Error: source_resource_id was not found in the request body."})

    def test_error_400_source_id_cant_be_none(self):
        """
        Return a 400 if the POST fails because the source_resource_id is missing from the request body.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.post(url, {
            "source_target_name": "curate_nd",
            "source_resource_id": "",
            "keywords": []}, **self.headers, format='json')
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "PresQT Error: source_resource_id can't be None or blank."})

    def test_error_400_no_keyword_action(self):
        """
        Return a 400 if the POST fails because "'presqt-keyword-action' missing in headers.
        """
        headers = self.headers
        headers.pop('HTTP_PRESQT_KEYWORD_ACTION')
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.post(url, {
            "source_target_name": "curate_nd",
            "source_resource_id": "dj52w379504",
            "keywords": []}, **headers, format='json')
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "PresQT Error: 'presqt-keyword-action' missing in the request headers."})

    def test_error_400_invalid_keyword_action(self):
        """
        Return a 400 if the POST fails because an invalid 'keyword_action' header was given.
        """
        headers = self.headers
        headers['HTTP_PRESQT_KEYWORD_ACTION'] = 'bad_action'
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.post(url, {
            "source_target_name": "curate_nd",
            "source_resource_id": "dj52w379504",
            "keywords": []}, **headers, format='json')
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'error': "PresQT Error: 'bad_action' is not a valid keyword_action. The options are 'automatic' or 'manual'."})

    def test_error_404_source_target_name_invalid(self):
        """
        Returns a 404 if the source_target_name provided in the body is not a valid target name
        """
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.post(url, {
            "source_target_name": "bad_name",
            "source_resource_id": "dj52w379504",
            "keywords": []}, **self.headers, format='json')
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data, {'error': "PresQT Error: 'bad_name' is not a valid Target name."})

    def test_error_404_destination_target_name_invalid(self):
        """
        Returns a 404 if the destination_target_name provided in the body is not a valid target name
        """
        url = reverse('resource_collection', kwargs={'target_name': 'bad_name'})
        response = self.client.post(url, {
            "source_target_name": "osf",
            "source_resource_id": "dj52w379504",
            "keywords": []}, **self.headers, format='json')
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data, {'error': "PresQT Error: 'bad_name' is not a valid Target name."})

    def test_error_400_source_target_not_destination_action(self):
        """
        Return a 400 if the POST method fails because the destination_target_name requested does not supported
        this endpoint's action
        """
        json_file = open('presqt/api_v1/tests/resources/targets_test.json')

        with patch("builtins.open") as mock_file:
            mock_file.return_value = json_file
            url = reverse('resource',
                          kwargs={'target_name': 'test', 'resource_id': 'resource_id'})
            response = self.client.post(url, {
                "source_target_name": "osf",
                "source_resource_id": "dj52w379504",
                "keywords": []},
                **self.headers, format='json')
            # Verify the error status code and message
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.data,
                             {'error': "PresQT Error: 'test' does not support the action 'resource_transfer_in'."})

    def test_error_400_keywords_not_in_body(self):
        """
        Returns a 400 if no keywords found in request body
        """
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        response = self.client.post(url, {
            "source_target_name": "osf",
            "source_resource_id": "dj52w379504"}, **self.headers, format='json')
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {'error': "PresQT Error: keywords was not found in the request body."})

    def test_error_400_keywords_not_list(self):
        """
        Returns a 400 if keywords found in request body not in list format
        """
        url = reverse('resource_collection', kwargs={'target_name': 'github'})
        response = self.client.post(url, {
            "source_target_name": "osf",
            "source_resource_id": "dj52w379504",
            "keywords": "oops"}, **self.headers, format='json')
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {'error': "PresQT Error: keywords must be in list format."})
