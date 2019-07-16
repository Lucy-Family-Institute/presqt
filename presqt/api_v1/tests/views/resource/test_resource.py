import json
import multiprocessing
import os
import shutil
import uuid
import zipfile
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import TEST_USER_TOKEN
from presqt.api_v1.utilities import write_file, read_file
from presqt.api_v1.utilities.fixity.download_fixity_checker import download_fixity_checker
from presqt.api_v1.utilities.io.remove_path_contents import remove_path_contents
from presqt.api_v1.utilities.multiprocess.watchdog import process_watchdog
from presqt.api_v1.views.resource.resource import Resource


class TestResourceGET(TestCase):
    """
    Test the endpoint's GET method for
    `api_v1/targets/{target_name}/resources/{resource_id}.{resource_format}/`
    """
    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': TEST_USER_TOKEN}

    def test_get_400_bad_resource_format(self):
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


class TestResourceGETJSON(TestCase):
    """
    Test the `api_v1/targets/{target_name}/resources/{resource_id}.json/` endpoint's GET method.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': TEST_USER_TOKEN}
        self.keys = ['kind', 'kind_name', 'id', 'title', 'date_created',
                     'date_modified', 'size', 'hashes', 'extra']

    def test_get_success_osf_project(self):
        """
        Return a 200 if the GET method is successful when grabbing an OSF resource that's a project.
        """
        resource_id = 'cmn5z'
        extra_keys = ['category', 'fork', 'current_user_is_contributor', 'preprint',
                       'current_user_permissions', 'custom_citation', 'collection', 'public',
                      'subjects', 'registration', 'current_user_can_comment', 'wiki_enabled',
                      'node_license', 'tags']

        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        self.assertListEqual(extra_keys, list(response.data['extra'].keys()))
        # Spot check some individual fields
        self.assertEqual('project', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('Test Project', response.data['title'])

    def test_get_success_osf_file(self):
        """
        Return a 200 if the GET method is successful when grabbing an OSF resource that's a file.
        """
        resource_id = '5cd9831c054f5b001a5ca2af'
        extra_keys = ['last_touched', 'materialized_path', 'current_version', 'provider', 'path',
                      'current_user_can_comment', 'guid', 'checkout', 'tags']
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        self.assertListEqual(extra_keys, list(response.data['extra'].keys()))
        # Spot check some individual fields
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('file', response.data['kind_name'])
        self.assertEqual('2017-01-27 PresQT Workshop Planning Meeting Items.docx',
                         response.data['title'])

    def test_get_success_osf_folder(self):
        """
        Return a 200 if the GET method is successful when grabbing an OSF resource that's a folder.
        """
        resource_id = '5cd9895b840cae001a708c31'
        extra_keys = ['last_touched', 'materialized_path', 'current_version', 'provider', 'path',
                      'current_user_can_comment', 'guid', 'checkout', 'tags']
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        self.assertListEqual(extra_keys, list(response.data['extra'].keys()))
        # Spot check some individual fields
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('folder', response.data['kind_name'])
        self.assertEqual('Docs', response.data['title'])

    def test_get_success_osf_storage(self):
        """
        Return a 200 if the GET method is successful when grabbing an OSF resource that's a storage.
        """
        resource_id = 'cmn5z:osfstorage'
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        # Verify that the extra field is empty for storage.
        self.assertEqual({}, response.data['extra'])
        # Spot check some individual fields
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('storage', response.data['kind_name'])
        self.assertEqual('osfstorage', response.data['title'])

    def test_get_error_400_missing_token_osf(self):
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

    def test_get_error_400_target_not_supported_test_target(self):
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

    def test_get_error_401_invalid_token_osf(self):
        """`
`       Return a 401 if the token provided is not a valid token.
        """
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'bad_token'}
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': 'cmn5z',
                                          'resource_format': 'json'})
        response = self.client.get(url, **header)

        # Verify the error status code and message
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "Token is invalid. Response returned a 401 status code."})

    def test_get_error_403_not_authorized_osf(self):
        """
        Return a 403 if the GET method fails because the user doesn't have access to this resource.
        """
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': 'q5xmw',
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data,
            {'error': "User does not have access to this resource with the token provided."})

    def test_get_error_404_bad_target_name_osf(self):
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

    def test_get_error_404_file_id_doesnt_exist_osf(self):
        """
        Return a 404 if the GET method fails because the file_id given does not map to a resource.
        """
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': '1234',
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data,
                         {'error': "Resource with id '1234' not found for this user."})

    def test_get_error_404_bad_storage_provider_osf(self):
        """
        Return a 404 if the GET method fails because a bad storage provider name was given in the
        storage ID
        """
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': 'cmn5z:badstorage',
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data,
                         {'error': "Resource with id 'cmn5z:badstorage' not found for this user."})

    def test_get_error_410_bad_resource_no_longer_exists_osf(self):
        """
        Return a 410 if the GET method fails because the resource requested no longer exists.
        """
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': '5cd989c5f8214b00188af9b5',
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.data,
                         {'error': "The requested resource is no longer available."})


class TestResourceGETZip(TestCase):
    """
    Test the `api_v1/targets/{target_name}/resources/{resource_id}.zip/` endpoint's GET method.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': TEST_USER_TOKEN}

    def shared_get_success_function_202(self):
        """
        This function will be used by tests that successfully hit the resource GET endpoint.
        It uses class attributes that are set in the test methods.

        Returns
        -------
        Fixity JSON from the fixity_info.json file
        """
        url = reverse('resource', kwargs={'target_name': self.target_name,
                                                  'resource_id': self.resource_id,
                                                  'resource_format': 'zip'})
        response = self.client.get(url, **self.header)
        # Verify the status code and content
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        # Verify the final status in the process_info file is 'finished'
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'finished')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(self.resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), self.file_number)

        # Since the coverage package does not pick up the multiprocessing, we will run the
        # 'download_resource' function manually with the same parameters that the multiprocess
        # version ran and run the same exact checks.

        # First we need to remove the contents of the ticket path except 'process_info.json'
        remove_path_contents(ticket_path, 'process_info.json')
        process_info_path = '{}/process_info.json'.format(ticket_path)
        # Call the download_resource manually
        process_state = multiprocessing.Value('b', 0)
        Resource._download_resource('osf', 'resource_download', TEST_USER_TOKEN,
                          self.resource_id, ticket_path, process_info_path, process_state)

        # Verify the final status in the process_info file is 'finished'
        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(final_process_info['status'], 'finished')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(self.resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), self.file_number)

        # Verify that the resource we expect is there.
        self.assertEqual(os.path.isfile('{}/{}/data/{}'.format(
            ticket_path, base_name, self.file_name)), True)

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

        # Return fixity info JSON
        fixity_file = zip_file.open('{}/data/fixity_info.json'.format(base_name))
        return json.load(fixity_file)

    def shared_get_success_function_202_with_error(self):
        """
        This function will be used by tests that successfully hit the GET resource endpoint but
        fail during the Resource._download_resource function.
        It uses class attributes that are set in the test methods.
        """
        url = reverse('resource', kwargs={'target_name': self.target_name,
                                                  'resource_id': self.resource_id,
                                                  'resource_format': 'zip'})
        response = self.client.get(url, **self.header)
        # Verify the status code and content
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(
                    'mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        # Since the coverage package does not pick up the multiprocessing, we will run the
        # 'Resource._download_resource' function manually with the same parameters that the
        # multiprocess version ran. And run the same exact checks.

        # First we need to remove the contents of the ticket path except 'process_info.json'
        remove_path_contents(ticket_path, 'process_info.json')
        process_info_path = '{}/process_info.json'.format(ticket_path)
        # Call the Resource._download_resource manually
        process_state = multiprocessing.Value('b', 0)
        Resource._download_resource('osf', 'resource_download', self.header['HTTP_PRESQT_SOURCE_TOKEN'],
                          self.resource_id, ticket_path, process_info_path, process_state)

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)

        # Verify that the zip file doesn't exist
        base_name = 'osf_download_{}'.format(self.resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        self.assertEqual(os.path.isfile(zip_path), False)

        # Verify the final status in the process_info file is 'failed'
        self.assertEqual(final_process_info['status'], 'failed')
        self.assertEqual(final_process_info['message'], self.status_message)
        self.assertEqual(final_process_info['status_code'], self.status_code)

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_get_success_202_file_osfstorage_jpg_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF
        resource file of type '.jpg'.
        """
        self.hashes = {
            "sha256": "3e517cda95ddbfcb270ab273201517f5ae0ee1190a9c5f6f7e6662f97868366f",
            "md5": "9e79fdd9032629743fca52634ecdfd86"
        }
        self.resource_id = '5cd98510f244ec001fe5632f'
        self.target_name = 'osf'
        self.file_number = 12
        self.file_name = '22776439564_7edbed7e10_o.jpg'
        fixity_info = self.shared_get_success_function_202()

        # Verify the fixity info returned is correct
        self.assertEqual(fixity_info[0]['fixity'], True)
        self.assertEqual(fixity_info[0]['fixity_details'],
                         'Source Hash and PresQT Calculated hash matched.')
        self.assertEqual(fixity_info[0]['hash_algorithm'], 'sha256')
        self.assertEqual(fixity_info[0]['presqt_hash'], self.hashes['sha256'])
        self.assertEqual(fixity_info[0]['source_hash'], self.hashes['sha256'])

    def test_get_success_202_file_osfstorage_docx_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF
        resource file of type '.docx'.
        """
        self.hashes = {
            "sha256": "a64091e8b8f3659184a4d4ba13adca36347aa8b981ee6c672bd2bd3a014c5a0c",
            "md5": "1f67b72a90b524873a26cd5d2671d0ef"
        }
        self.resource_id = '5cd98978054f5b001a5ca746'
        self.target_name = 'osf'
        self.file_number = 12
        self.file_name = 'build-plugins.js'
        fixity_info = self.shared_get_success_function_202()

        # Verify the fixity info returned is correct
        self.assertEqual(fixity_info[0]['fixity'], True)
        self.assertEqual(fixity_info[0]['fixity_details'],
                         'Source Hash and PresQT Calculated hash matched.')
        self.assertEqual(fixity_info[0]['hash_algorithm'], 'sha256')
        self.assertEqual(fixity_info[0]['presqt_hash'], self.hashes['sha256'])
        self.assertEqual(fixity_info[0]['source_hash'], self.hashes['sha256'])

    def test_get_success_202_file_osfstorage_pdf_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF
        resource file of type '.pdf'.
        """
        self.hashes = {
            "sha256": "343e249fdb0818a58edcc64663e1eb116843b4e1c4e74790ff331628593c02be",
            "md5": "a4536efb47b26eaf509edfdaca442037"
        }
        self.resource_id = '5cd98978f244ec001ee86609'
        self.target_name = 'osf'
        self.file_number = 12
        self.file_name = 'Character Sheet - Alternative - Print Version.pdf'
        fixity_info = self.shared_get_success_function_202()

        # Verify the fixity info returned is correct
        self.assertEqual(fixity_info[0]['fixity'], True)
        self.assertEqual(fixity_info[0]['fixity_details'],
                         'Source Hash and PresQT Calculated hash matched.')
        self.assertEqual(fixity_info[0]['hash_algorithm'], 'sha256')
        self.assertEqual(fixity_info[0]['presqt_hash'], self.hashes['sha256'])
        self.assertEqual(fixity_info[0]['source_hash'], self.hashes['sha256'])

    def test_get_success_202_file_osfstorage_mp3_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF
        resource file of type '.mp3'.
        """
        self.hashes = {
            "sha256": "fe3e904fbd549a3ac014bc26fb3d5042d58759f639f24e745dba3580ea316850",
            "md5": "845248e5456033c6df85b5cffcd7ea8a"
        }
        self.resource_id = '5cd98979f8214b00198b1153'
        self.target_name = 'osf'
        self.file_number = 12
        self.file_name = '02 - The Widow.mp3'
        fixity_info = self.shared_get_success_function_202()

        # Verify the fixity info returned is correct
        self.assertEqual(fixity_info[0]['fixity'], True)
        self.assertEqual(fixity_info[0]['fixity_details'],
                         'Source Hash and PresQT Calculated hash matched.')
        self.assertEqual(fixity_info[0]['hash_algorithm'], 'sha256')
        self.assertEqual(fixity_info[0]['presqt_hash'], self.hashes['sha256'])
        self.assertEqual(fixity_info[0]['source_hash'], self.hashes['sha256'])

    def test_get_success_202_file_googledrive_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF resource
        from a storage provider with no hashes.
        """
        self.resource_id = '5cd98a30f2c01100177156be'
        self.target_name = 'osf'
        self.file_number = 12
        self.file_name = 'Character Sheet - Alternative - Print Version.pdf'
        fixity_info = self.shared_get_success_function_202()

        # Verify the fixity info returned is correct
        self.assertEqual(fixity_info[0]['fixity'], None)
        self.assertEqual(fixity_info[0]['fixity_details'],
                         'Either a Source Hash was not provided or the source hash algorithm is not supported.')
        self.assertEqual(fixity_info[0]['hash_algorithm'], 'md5')
        self.assertEqual(fixity_info[0]['source_hash'], None)

    def test_get_success_202_folder_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF resource folder
        """
        self.resource_id = '5cd98b0af244ec0021e5f8dd'
        self.target_name = 'osf'
        self.file_number = 14
        self.file_name = 'Docs2/Docs3/CODE_OF_CONDUCT.md'
        final_process_info = self.shared_get_success_function_202()

        for zjson in final_process_info:
            self.assertEqual(zjson['fixity'], True)

    def test_get_success_202_storage_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF resource storage
        """
        self.resource_id = 'cmn5z:googledrive'
        self.target_name = 'osf'
        self.file_number = 15
        self.file_name = 'googledrive/Google Images/IMG_4740.jpg'
        final_process_info = self.shared_get_success_function_202()

        # Verify the fixity info returned is correct
        for zjson in final_process_info:
            self.assertEqual(zjson['fixity'], None)

    def test_get_success_202_project_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF resource project
        """
        self.resource_id = 'cmn5z'
        self.target_name = 'osf'
        self.file_number = 71
        self.file_name = 'Test Project/osfstorage/Docs/Docs2/Docs3/CODE_OF_CONDUCT.md'
        self.shared_get_success_function_202()

    def test_get_error_400_missing_token_osf(self):
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

    def test_get_error_400_target_not_supported_test_target(self):
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

    def test_get_error_404_bad_target_name_osf(self):
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

    def test_get_202_downloadresource_fails_file_id_doesnt_exist_osf(self):
        """
        Return a 202 if the GET method succeeds but the Resource._download_resource function fails
        because the file_id given does not map to a resource.
        """
        self.resource_id = '1234'
        self.target_name = 'osf'
        self.status_code = 404
        self.status_message = "Resource with id '1234' not found for this user."
        self.shared_get_success_function_202_with_error()

    def test_get_202_downloadresource_fails_bad_storage_provider_osf(self):
        """
        Return a 202 if the GET method succeeds but the Resource._download_resource function fails
        because a bad storage provider name was given in the storage ID
        """
        self.resource_id = 'cmn5z:badstorage'
        self.target_name = 'osf'
        self.status_code = 404
        self.status_message = "Resource with id 'cmn5z:badstorage' not found for this user."
        self.shared_get_success_function_202_with_error()

    def test_get_202_downloadresource_fails_not_authorized_osf(self):
        """
        Return a 200 if the GET method succeeds but the Resource._download_resource function fails because
        the user doesn't have access to this resource.
        """
        self.resource_id = 'q5xmw'
        self.target_name = 'osf'
        self.status_code = 403
        self.status_message = "User does not have access to this resource with the token provided."
        self.shared_get_success_function_202_with_error()

    def test_get_202_downloadresource_fails_invalid_token_osf(self):
        """
        Return a 202 if the GET method succeeds but the Resource._download_resource function fails
        because the token provided is not a valid token.
        """
        self.resource_id = 'cmn5z'
        self.target_name = 'osf'
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': 'bad_token'}
        self.status_code = 401
        self.status_message = "Token is invalid. Response returned a 401 status code."
        self.shared_get_success_function_202_with_error()

    def test_200_success_fixity_failed_osf(self):
        """
        Since both the file and hashes are coming from OSF API calls we don't have the opportunity
            to corrupt the file or change the expected hashes before running the fixity checker.
            To solve this the test will have two parts:
            1. The first part will be verifying that the fixity checker function will throw an
                error if given a file and a mismatched hash dictionary.

        """
        hashes = {
            "sha256": "bad_hash",
            "md5": "bad_hash"
        }
        resource_id = '5cd98510f244ec001fe5632f'
        url = reverse('resource', kwargs={'target_name': 'osf',
                                                  'resource_id': resource_id,
                                                  'resource_format': 'zip'})
        response = self.client.get(url, **self.header)
        # Verify the status code and content
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(
                    'mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        # Verify the final status in the process_info file is 'finished'
        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(final_process_info['status'], 'finished')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        # Verify that the zip file exists and it holds the correct number of files.
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), 12)

        # Grab the .jpg file in the zip and run it back through the fixity checker with bad hashes
        # So we can get a failed fixity. This fixity variable will be used later in our Patch.
        fixity = download_fixity_checker(
            read_file('{}/{}/data/22776439564_7edbed7e10_o.jpg'.format(ticket_path, base_name)),
            hashes)

        # Since the coverage package does not pick up the multiprocessing, we will run the
        # 'Resource._download_resource' function manually with the same parameters that the
        # multiprocess version ran. And run the same exact checks.

        # First we need to remove the contents of the ticket path except 'process_info.json'
        remove_path_contents(ticket_path, 'process_info.json')
        process_info_path = '{}/process_info.json'.format(ticket_path)

        self.assertEqual(fixity['fixity'], False)

        # Patch the fixity_checker() function to return our bad fixity dictionary.
        with patch('presqt.api_v1.utilities.fixity.download_fixity_checker.download_fixity_checker') as fake_send:
            # Manually verify the fixity_checker will fail
            fake_send.return_value = fixity
            process_state = multiprocessing.Value('b', 0)
            Resource._download_resource('osf', 'resource_download', TEST_USER_TOKEN,
                              resource_id, ticket_path, process_info_path, process_state)

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'finished'
        self.assertEqual(final_process_info['status'], 'finished')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), 12)

        # Verify that the resource we expect is there.
        self.assertEqual(
            os.path.isfile(
                '{}/{}/data/22776439564_7edbed7e10_o.jpg'.format(ticket_path, base_name)), True)

        # Verify the fixity info returned is correct
        fixity_file = zip_file.open('{}/data/fixity_info.json'.format(base_name))
        fixity_info = json.load(fixity_file)
        self.assertEqual(fixity_info[0]['fixity'], False)
        self.assertEqual(fixity_info[0]['fixity_details'],
                         'Source Hash and PresQT Calculated hash do not match.')
        self.assertEqual(fixity_info[0]['hash_algorithm'], 'sha256')
        self.assertEqual(fixity_info[0]['source_hash'], hashes['sha256'])
        self.assertNotEqual(fixity_info[0]['presqt_hash'], hashes['sha256'])

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_process_watchdog_success_osf(self):
        """
        Manually test the process_watchdog utility function to get code coverage and make sure it
        is working as expected.
        """
        resource_id = '5cd98510f244ec001fe5632f'
        ticket_number = uuid.uuid4()
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)
        process_info_path = 'mediafiles/downloads/{}/process_info.json'.format(ticket_number)
        process_info_obj = {
            'presqt-source-token': TEST_USER_TOKEN,
            'status': 'in_progress',
            'expiration': str(timezone.now() + relativedelta(days=5)),
            'message': 'Download is being processed on the server',
            'status_code': None
        }
        write_file(process_info_path, process_info_obj, True)
        # Start the Resource._download_resource process manually
        process_state = multiprocessing.Value('b', 0)
        function_process = multiprocessing.Process(target=Resource._download_resource, args=[
            'osf', 'resource_download', TEST_USER_TOKEN, resource_id,
            ticket_path, process_info_path, process_state])
        function_process.start()

        # start watchdog function manually
        process_watchdog(function_process, process_info_path, 3600, process_state)

        # Make sure the watchdog didn't overwrite the file and its status si still 'finished'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'finished')

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_process_watchdog_failure_osf(self):
        """
        Manually test the process_watchdog utility function to get code coverage and make sure it
        is working as expected.
        Test whether the process_watchdog catches that the monitored process took too long.
        """
        resource_id = '5cd9832cf244ec0021e5f245'
        ticket_number = uuid.uuid4()
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)
        process_info_path = 'mediafiles/downloads/{}/process_info.json'.format(ticket_number)
        process_info_obj = {
            'presqt-source-token': TEST_USER_TOKEN,
            'status': 'in_progress',
            'expiration': str(timezone.now() + relativedelta(days=5)),
            'message': 'Download is being processed on the server',
            'status_code': None
        }
        write_file(process_info_path, process_info_obj, True)

        # Start the Resource._download_resource process manually
        process_state = multiprocessing.Value('b', 0)
        function_process = multiprocessing.Process(target=Resource._download_resource, args=[
            'osf', 'resource_download', TEST_USER_TOKEN, resource_id,
            ticket_path, process_info_path, process_state])
        function_process.start()

        # start watchdog function manually
        process_watchdog(function_process, process_info_path, 1, process_state)

        # Make sure the process_watchdog reached a failure and updated the status to 'failed'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'failed')
        self.assertEqual(process_info['status_code'], 504)
        self.assertEqual(process_info['message'], 'The process took too long on the server.')

        # Delete corresponding folder
        shutil.rmtree(ticket_path)


class TestResourcePOST(TestCase):
    """
    Test the endpoint's POST method for resource uploads:
         `api_v1/targets/{target_name}/resources/{resource_id}/`
         `api_v1/targets/{target_name}/resources/`
    """

    def setUp(self):
        self.client = APIClient()
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': TEST_USER_TOKEN}
        self.good_zip_file = 'presqt/api_v1/tests/resources/upload/good_bagit.zip'
    def tearDown(self):
        # Delete project
        pass

    def test_post_success_202_upload_osf(self):
        """
        This test is more of an integration test rather than a unit test.
        Since order of requests is important, it will test several POST requests to verify the files
        are properly ignored/replaced:

        Return a 202 when uploading a new top level container.
        Return a 202 when uploading to an existing container with duplicate files ignored.
        Return a 202 when uploading to an existing container with duplicate files replaced.
        """
        self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = 'ignore'

        #### 202 when uploading a new top level container ###
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.post(url, {'presqt-file': open('presqt/api_v1/tests/resources/upload/new_project.zip', 'rb')}, **self.headers)

        # Verify status code and message
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['message'], 'The server is processing the request.')

        # #### Return a 202 when uploading to an existing container with duplicate files ignored ####
        # #### Return a 202 when uploading to an existing container with duplicate files replaced ####
        # # Make the initial upload of files
        # url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 's7dvn'})
        # response = self.client.post(url, {'presqt-file': open(self.good_zip_file, 'rb')}, **self.headers)
        #
        # # Verify status code and message
        # self.assertEqual(response.status_code, 202)
        # self.assertEqual(response.data['message'], 'The server is processing the request.')
        #
        # ticket_number = response.data['ticket_number']
        # ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)
        #
        # # Verify process_info file status is 'in_progress' initially
        # process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # self.assertEqual(process_info['status'], 'in_progress')
        #
        # # Wait until the spawned off process finishes in the background to do further validation
        # while process_info['status'] == 'in_progress':
        #     try:
        #         process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        #     except json.decoder.JSONDecodeError:
        #         # Pass while the process_info file is being written to
        #         pass
        #
        # # Verify process_info.json file data
        # process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # print(process_info)
        # self.assertEqual(process_info['status'], 'finished')
        # self.assertEqual(process_info['message'], 'Upload successful')
        # self.assertEqual(process_info['status_code'], '200')
        # self.assertEqual(process_info['failed_fixity'], [])
        # self.assertEqual(process_info['hash_algorithm'], 'sha256')

        # DELETE PROJECT FROM OSF



    # 202 Upload file to container
    # 202 Upload project to container
    # 202 Upload storage to container
    # 202 Upload new project
    # 400 "'new_target' does not support the action 'resource_upload'."
    # 400 "'presqt-destination-token' missing in the request headers."
    # 400 "The file, 'presqt-file', is not found in the body of the request."
    # 400 "The file provided, 'presqt-file', is not a zip file."
    # 400 "The file provided is not in BagIt format."
    #       - missing file
    #       - unknown file
    #       - mismatched hashes
    # 400 "Checksums failed to validate."
    # 400 "'presqt-file-duplicate-action' missing in the request headers."
    # 400 "'bad_action' is not a valid file_duplicate_action. The options are 'ignore' or 'update'."
    # 401 "Token is invalid. Response returned a 401 status code."
    # 403 "User does not have access to this resource with the token provided."
    # 404 "'bad_target' is not a valid Target name."
    # 404 "error": "Resource with id 'bad_id' not found for this user."
    # 410 "error": "The requested resource is no longer available."
