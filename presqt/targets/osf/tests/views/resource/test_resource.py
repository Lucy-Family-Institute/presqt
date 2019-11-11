import json
import multiprocessing
import os
import shutil
import uuid
import zipfile
from unittest import mock
from unittest.mock import patch

import requests
from dateutil.relativedelta import relativedelta
from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import OSF_TEST_USER_TOKEN, OSF_UPLOAD_TEST_USER_TOKEN

from presqt.api_v1.utilities.fixity.download_fixity_checker import download_fixity_checker
from presqt.api_v1.utilities.multiprocess.watchdog import process_watchdog
from presqt.api_v1.views.resource.base_resource import BaseResource
from presqt.json_schemas.schema_handlers import schema_validator
from presqt.targets.osf.functions.upload_metadata import osf_upload_metadata
from presqt.targets.osf.utilities import delete_users_projects
from presqt.targets.utilities import (shared_get_success_function_202,
                                      shared_get_success_function_202_with_error, process_wait,
                                      shared_upload_function_osf)
from presqt.utilities import (
    write_file, read_file, get_dictionary_from_list, remove_path_contents, PresQTError)


class TestResourceGETJSON(SimpleTestCase):
    """
    Test the `api_v1/targets/osf/resources/{resource_id}.json/` endpoint's GET method.

    Testing OSF integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN}
        self.keys = ['kind', 'kind_name', 'id', 'title', 'date_created',
                     'date_modified', 'hashes', 'extra', 'links', 'actions']

    def test_success_project(self):
        """
        Return a 200 if the GET method is successful when grabbing an OSF resource that's a project.
        """
        resource_id = 'cmn5z'
        extra_keys = ['category', 'fork', 'current_user_is_contributor', 'preprint',
                      'current_user_permissions', 'custom_citation', 'collection', 'public',
                      'subjects', 'registration', 'current_user_can_comment', 'wiki_enabled',
                      'node_license', 'tags', 'size']

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
        for link in response.data['links']:
            if link['name'] == 'Download':
                self.assertEqual(link['method'], 'GET')
            if link['name'] == 'Upload':
                self.assertEqual(link['method'], 'POST')
        self.assertEqual(len(response.data['links']), 3)

    def test_success_file(self):
        """
        Return a 200 if the GET method is successful when grabbing an OSF resource that's a file.
        """
        resource_id = '5cd9831c054f5b001a5ca2af'
        extra_keys = ['last_touched', 'materialized_path', 'current_version', 'provider', 'path',
                      'current_user_can_comment', 'guid', 'checkout', 'tags', 'size']
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
        self.assertEqual(len(response.data['links']), 1)
        self.assertEqual(response.data['links'][0]['name'], 'Download')

    def test_success_file_no_format(self):
        """
        Return a 200 if the GET method is successful when grabbing an OSF resource that's a file.
        """
        resource_id = '5cd9831c054f5b001a5ca2af'
        extra_keys = ['last_touched', 'materialized_path', 'current_version', 'provider', 'path',
                      'current_user_can_comment', 'guid', 'checkout', 'tags', 'size']
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
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

    def test_success_folder(self):
        """
        Return a 200 if the GET method is successful when grabbing an OSF resource that's a folder.
        """
        resource_id = '5cd9895b840cae001a708c31'
        extra_keys = ['last_touched', 'materialized_path', 'current_version', 'provider', 'path',
                      'current_user_can_comment', 'guid', 'checkout', 'tags', 'size']
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

    def test_success_storage(self):
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

    def test_error_401_invalid_token(self):
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

    def test_error_403_not_authorized(self):
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

    def test_error_404_file_id_doesnt_exist(self):
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

    def test_error_404_bad_storage_provider(self):
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

    def test_error_410_bad_resource_no_longer_exists(self):
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


class TestResourceGETZip(SimpleTestCase):
    """
    Test the `api_v1/targets/osf/resources/{resource_id}.zip/` endpoint's GET method.

    Testing OSF integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN}

    def test_success_202_file_osfstorage_jpg(self):
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
        self.file_number = 13
        self.file_name = '22776439564_7edbed7e10_o.jpg'
        fixity_info = shared_get_success_function_202(self)

        # Verify the fixity info returned is correct
        self.assertEqual(fixity_info[0]['fixity'], True)
        self.assertEqual(fixity_info[0]['fixity_details'],
                         'Source Hash and PresQT Calculated hash matched.')
        self.assertEqual(fixity_info[0]['hash_algorithm'], 'sha256')
        self.assertEqual(fixity_info[0]['presqt_hash'], self.hashes['sha256'])
        self.assertEqual(fixity_info[0]['source_hash'], self.hashes['sha256'])

    def test_success_202_file_osfstorage_docx(self):
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
        self.file_number = 13
        self.file_name = 'build-plugins.js'
        fixity_info = shared_get_success_function_202(self)

        # Verify the fixity info returned is correct
        self.assertEqual(fixity_info[0]['fixity'], True)
        self.assertEqual(fixity_info[0]['fixity_details'],
                         'Source Hash and PresQT Calculated hash matched.')
        self.assertEqual(fixity_info[0]['hash_algorithm'], 'sha256')
        self.assertEqual(fixity_info[0]['presqt_hash'], self.hashes['sha256'])
        self.assertEqual(fixity_info[0]['source_hash'], self.hashes['sha256'])

    def test_success_202_file_osfstorage_pdf(self):
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
        self.file_number = 13
        self.file_name = 'Character Sheet - Alternative - Print Version.pdf'
        fixity_info = shared_get_success_function_202(self)

        # Verify the fixity info returned is correct
        self.assertEqual(fixity_info[0]['fixity'], True)
        self.assertEqual(fixity_info[0]['fixity_details'],
                         'Source Hash and PresQT Calculated hash matched.')
        self.assertEqual(fixity_info[0]['hash_algorithm'], 'sha256')
        self.assertEqual(fixity_info[0]['presqt_hash'], self.hashes['sha256'])
        self.assertEqual(fixity_info[0]['source_hash'], self.hashes['sha256'])

    def test_success_202_file_osfstorage_mp3(self):
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
        self.file_number = 13
        self.file_name = '02 - The Widow.mp3'
        fixity_info = shared_get_success_function_202(self)

        # Verify the fixity info returned is correct
        self.assertEqual(fixity_info[0]['fixity'], True)
        self.assertEqual(fixity_info[0]['fixity_details'],
                         'Source Hash and PresQT Calculated hash matched.')
        self.assertEqual(fixity_info[0]['hash_algorithm'], 'sha256')
        self.assertEqual(fixity_info[0]['presqt_hash'], self.hashes['sha256'])
        self.assertEqual(fixity_info[0]['source_hash'], self.hashes['sha256'])

    def test_success_202_file_googledrive(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF resource
        from a storage provider with no hashes.
        """
        self.resource_id = '5cd98a30f2c01100177156be'
        self.target_name = 'osf'
        self.file_number = 13
        self.file_name = 'Character Sheet - Alternative - Print Version.pdf'
        fixity_info = shared_get_success_function_202(self)

        # Verify the fixity info returned is correct
        self.assertEqual(fixity_info[0]['fixity'], None)
        self.assertEqual(fixity_info[0]['fixity_details'],
                         'Either a Source Hash was not provided or the source hash algorithm is not supported.')
        self.assertEqual(fixity_info[0]['hash_algorithm'], 'md5')
        self.assertEqual(fixity_info[0]['source_hash'], None)

    def test_success_202_folder(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF resource folder
        """
        self.resource_id = '5cd98b0af244ec0021e5f8dd'
        self.target_name = 'osf'
        self.file_number = 15
        self.file_name = 'Docs2/Docs3/CODE_OF_CONDUCT.md'
        final_process_info = shared_get_success_function_202(self)

        for zjson in final_process_info:
            self.assertEqual(zjson['fixity'], True)

    def test_success_202_storage(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF resource storage
        """
        self.resource_id = 'cmn5z:googledrive'
        self.target_name = 'osf'
        self.file_number = 16
        self.file_name = 'googledrive/Google Images/IMG_4740.jpg'
        final_process_info = shared_get_success_function_202(self)

        # Verify the fixity info returned is correct
        for zjson in final_process_info:
            self.assertEqual(zjson['fixity'], None)

    def test_success_202_project(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF resource project
        """
        self.resource_id = 'cmn5z'
        self.target_name = 'osf'
        self.file_number = 77
        self.file_name = 'Test Project/osfstorage/Docs/Docs2/Docs3/CODE_OF_CONDUCT.md'
        shared_get_success_function_202(self)

        # Verify empty folders have been written to zip file
        list_of_empty_folders = ['osf_download_cmn5z/data/Test Project/osfstorage/Empty Folder 2/',
                                 'osf_download_cmn5z/data/Test Project/Sub Test Project/osfstorage/']
        for empty_folder in list_of_empty_folders:
            self.assertIn(empty_folder, self.zip_file.namelist())

    def test_202_downloadresource_fails_file_id_doesnt_exist(self):
        """
        Return a 202 if the GET method succeeds but the Resource._download_resource function fails
        because the file_id given does not map to a resource.
        """
        self.resource_id = '1234'
        self.target_name = 'osf'
        self.status_code = 404
        self.status_message = "Resource with id '1234' not found for this user."
        shared_get_success_function_202_with_error(self)

    def test_202_downloadresource_fails_bad_storage_provider(self):
        """
        Return a 202 if the GET method succeeds but the Resource._download_resource function fails
        because a bad storage provider name was given in the storage ID
        """
        self.resource_id = 'cmn5z:badstorage'
        self.target_name = 'osf'
        self.status_code = 404
        self.status_message = "Resource with id 'cmn5z:badstorage' not found for this user."
        shared_get_success_function_202_with_error(self)

    def test_202_downloadresource_fails_not_authorized(self):
        """
        Return a 200 if the GET method succeeds but the Resource._download_resource function fails because
        the user doesn't have access to this resource.
        """
        self.resource_id = 'q5xmw'
        self.target_name = 'osf'
        self.status_code = 403
        self.status_message = "User does not have access to this resource with the token provided."
        shared_get_success_function_202_with_error(self)

    def test_202_downloadresource_fails_invalid_token(self):
        """
        Return a 202 if the GET method succeeds but the Resource._download_resource function fails
        because the token provided is not a valid token.
        """
        self.resource_id = 'cmn5z'
        self.target_name = 'osf'
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': 'bad_token'}
        self.status_code = 401
        self.status_message = "Token is invalid. Response returned a 401 status code."
        shared_get_success_function_202_with_error(self)

    def test_200_success_fixity_failed(self):
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
        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(final_process_info['status'], 'finished')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        # Verify that the zip file exists and it holds the correct number of files.
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), 13)

        # Grab the .jpg file in the zip and run it back through the fixity checker with bad hashes
        # So we can get a failed fixity. This fixity variable will be used later in our Patch.

        resource_dict = {
            "file": read_file('{}/{}/data/22776439564_7edbed7e10_o.jpg'.format(ticket_path, base_name)),
            "hashes": hashes,
            "title": 'data/22776439564_7edbed7e10_o.jpg',
            "path": '{}/{}/data/22776439564_7edbed7e10_o.jpg'.format(ticket_path, base_name),
            "metadata": {}
        }
        fixity, fixity_match = download_fixity_checker(resource_dict)

        # First we need to remove the contents of the ticket path except 'process_info.json'
        remove_path_contents(ticket_path, 'process_info.json')
        process_info_path = '{}/process_info.json'.format(ticket_path)

        self.assertEqual(fixity['fixity'], False)

        # Patch the fixity_checker() function to return our bad fixity dictionary.
        with patch('presqt.api_v1.utilities.fixity.download_fixity_checker.download_fixity_checker') as fake_send:
            # Manually verify the fixity_checker will fail
            fake_send.return_value = fixity, fixity_match
            process_state = multiprocessing.Value('b', 0)

            # Create an instance of the BaseResource and add all of the appropriate class attributes
            # needed for _download_resource()
            resource_instance = BaseResource()
            resource_instance.source_target_name = 'osf'
            resource_instance.action = 'resource_download'
            resource_instance.source_token = OSF_TEST_USER_TOKEN
            resource_instance.source_resource_id = resource_id
            resource_instance.ticket_path = ticket_path
            resource_instance.resource_main_dir = '{}/{}'.format(ticket_path, base_name)
            resource_instance.process_info_path = process_info_path
            resource_instance.process_state = process_state
            resource_instance.process_info_obj = {}
            resource_instance.base_directory_name = base_name
            resource_instance._download_resource()

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'finished'
        self.assertEqual(final_process_info['status'], 'finished')
        # Verify that the message is what is expected if fixity has failed.
        self.assertEqual(final_process_info['message'],
                         'Download successful but with fixity errors.')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), 13)

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

    def test_process_watchdog_failure(self):
        """
        Manually test the process_watchdog utility function to get code coverage and make sure it
        is working as expected.
        Test whether the process_watchdog catches that the monitored process took too long.
        """
        resource_id = '5cd9832cf244ec0021e5f245'
        ticket_number = uuid.uuid4()
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)
        base_name = 'osf_download_{}'.format(resource_id)
        process_info_path = 'mediafiles/downloads/{}/process_info.json'.format(ticket_number)
        process_info_obj = {
            'presqt-source-token': OSF_TEST_USER_TOKEN,
            'status': 'in_progress',
            'expiration': str(timezone.now() + relativedelta(days=5)),
            'message': 'Download is being processed on the server',
            'status_code': None
        }
        write_file(process_info_path, process_info_obj, True)

        # Start the Resource._download_resource process manually
        process_state = multiprocessing.Value('b', 0)

        resource_instance = BaseResource()
        resource_instance.source_target_name = 'osf'
        resource_instance.action = 'resource_download'
        resource_instance.source_token = OSF_TEST_USER_TOKEN
        resource_instance.source_resource_id = resource_id
        resource_instance.ticket_path = ticket_path
        resource_instance.resource_main_dir = '{}/{}'.format(ticket_path, base_name)
        resource_instance.process_info_path = process_info_path
        resource_instance.process_state = process_state
        resource_instance.process_info_obj = {}
        resource_instance.base_directory_name = base_name
        function_process = multiprocessing.Process(target=resource_instance._download_resource)
        function_process.start()

        # Start watchdog function manually
        process_watchdog(function_process, process_info_path, 1, process_state)

        # Make sure the process_watchdog reached a failure and updated the status to 'failed'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'failed')
        self.assertEqual(process_info['status_code'], 504)
        self.assertEqual(process_info['message'], 'The process took too long on the server.')

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_metadata_success_no_existing_file(self):
        """
        Test that the metadata provided with the download is correct.
        Download a project that has no existing metadata file.
        """
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': '5cd98b0af244ec0021e5f8dd',
                                          'resource_format': 'zip'})
        response = self.client.get(url, **self.header)
        # Verify the status code and content
        self.assertEqual(response.status_code, 202)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        # Verify that the metadata file is there.
        metadata_path = '{}/osf_download_5cd98b0af244ec0021e5f8dd/data/PRESQT_FTS_METADATA.json'.\
            format(ticket_path)
        self.assertEqual(os.path.isfile(metadata_path), True)
        metadata_json = read_file(metadata_path, True)

        self.assertEqual(True, schema_validator(
            'presqt/json_schemas/metadata_schema.json', metadata_json))
        self.assertEqual(1, len(metadata_json['actions']))
        action_data = metadata_json['actions'][0]
        self.assertEqual(3, len(action_data['files']['created']))
        self.assertEqual(0, len(action_data['files']['updated']))
        self.assertEqual(0, len(action_data['files']['ignored']))
        self.assertEqual('resource_download', action_data['actionType'])
        self.assertEqual('osf', action_data['sourceTargetName'])
        self.assertEqual('Test User', action_data['sourceUsername'])
        self.assertEqual('Local Machine', action_data['destinationTargetName'])
        self.assertEqual(None, action_data['destinationUsername'])

        file_data = get_dictionary_from_list(
            action_data['files']['created'], 'title', 'CODE_OF_CONDUCT.md')
        self.assertEqual(
            '/Test Project/osfstorage/Docs/Docs2/Docs3/CODE_OF_CONDUCT.md', file_data['sourcePath'])
        self.assertEqual({'sha256': 'b6da113590fef57e2ba870df1b987084a2886cfa39378cff06fdb5a3271bc2be',
                          'md5': 'af30f9418b9fe2ad9c0e1f70286dfda0'}, file_data['sourceHashes'])
        self.assertEqual('/Docs2/Docs3/CODE_OF_CONDUCT.md', file_data['destinationPath'])
        self.assertEqual({}, file_data['destinationHashes'])

        file_data = get_dictionary_from_list(
            action_data['files']['created'], 'title', '02 - The Widow.mp3')
        self.assertEqual('/Test Project/osfstorage/Docs/Docs2/02 - The Widow.mp3',
                         file_data['sourcePath'])
        self.assertEqual({'sha256': 'fe3e904fbd549a3ac014bc26fb3d5042d58759f639f24e745dba3580ea316850',
                          'md5': '845248e5456033c6df85b5cffcd7ea8a'}, file_data['sourceHashes'])
        self.assertEqual('/Docs2/02 - The Widow.mp3', file_data['destinationPath'])
        self.assertEqual({}, file_data['destinationHashes'])

        file_data = get_dictionary_from_list(action_data['files']['created'], 'title',
                                             '_config.yml')
        self.assertEqual('/Test Project/osfstorage/Docs/Docs2/_config.yml',
                         file_data['sourcePath'])
        self.assertEqual({'sha256': '4a903798a005fecbfa07455fe0da45cd570df3ae058bb0537c583335bb0c47e3',
                          'md5': '84bddd5dcb51e8386e8c406aabd5057f'}, file_data['sourceHashes'])
        self.assertEqual('/Docs2/_config.yml', file_data['destinationPath'])
        self.assertEqual({}, file_data['destinationHashes'])

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_metadata_success_existing_file(self):
        """
        Download a resource that has an existing metadata file.
        Test that the metadata provided with the download is valid.
        """
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': 'cmn5z:osfstorage',
                                          'resource_format': 'zip'})
        response = self.client.get(url, **self.header)
        # Verify the status code and content
        self.assertEqual(response.status_code, 202)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        # Verify that the metadata file is there.
        metadata_path = '{}/osf_download_cmn5z:osfstorage/data/PRESQT_FTS_METADATA.json'. \
            format(ticket_path)
        self.assertEqual(os.path.isfile(metadata_path), True)
        metadata_json = read_file(metadata_path, True)

        self.assertEqual(True, schema_validator(
            'presqt/json_schemas/metadata_schema.json', metadata_json))
        self.assertEqual(2, len(metadata_json['actions']))

        for action in metadata_json['actions']:
            if action['id'] == 'd1b9df10-d7d4-4223-b49b-efa51bca16e1':
                self.assertEqual({"created": [], "updated": [], "ignored": []}, action['files'])
            else:
                self.assertEqual(57, len(action['files']['created']))

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_metadata_success_existing_invalid_file(self):
        """
        Download a resource that has an existing metadata file.
        Test that the metadata provided with the download is invalid.
        """
        url = reverse('resource', kwargs={'target_name': 'osf',
                                          'resource_id': '5cd988d3054f5b00185ca5e3',
                                          'resource_format': 'zip'})
        response = self.client.get(url, **self.header)
        # Verify the status code and content
        self.assertEqual(response.status_code, 202)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        # Verify that the invalid metadata file has been renamed
        metadata_path = '{}/osf_download_5cd988d3054f5b00185ca5e3/data/More Images/INVALID_PRESQT_FTS_METADATA.json'. \
            format(ticket_path)
        self.assertEqual(os.path.isfile(metadata_path), True)
        metadata_json = read_file(metadata_path, True)
        self.assertEqual([{"bad": "action"}], metadata_json['actions'])

        # Verify that the valid metadata file exists
        metadata_path = '{}/osf_download_5cd988d3054f5b00185ca5e3/data/PRESQT_FTS_METADATA.json'. \
            format(ticket_path)
        self.assertEqual(os.path.isfile(metadata_path), True)
        metadata_json = read_file(metadata_path, True)
        self.assertEqual(1, len(metadata_json['actions']))

        # Delete corresponding folder
        shutil.rmtree(ticket_path)


class TestResourcePOST(SimpleTestCase):
    """
    Test the endpoint's POST method for resource uploads:
         `api_v1/targets/{target_name}/resources/{resource_id}/`
         `api_v1/targets/{target_name}/resources/`

    Testing OSF integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.token = OSF_UPLOAD_TEST_USER_TOKEN
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': self.token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        self.good_zip_file = 'presqt/api_v1/tests/resources/upload/GoodBagIt.zip'

    # def tearDown(self):
    #     """
    #     This should run at the end of this test class
    #     """
    #     delete_users_projects(self.token)

    def test_success_202_upload(self):
        """
        This test is more of an integration test rather than a unit test.
        Since order of requests is important, it will test several POST requests to verify the files
        are properly ignored/replaced:

        Return a 202 when uploading a new top level container.
        Return a 202 when uploading to an existing container with duplicate files ignored.
        Return a 202 when uploading to an existing container with duplicate files replaced.
        """
        ######## 202 when uploading a new top level container ########
        self.resource_id = None
        self.duplicate_action = 'ignore'
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.resources_ignored = []
        self.resources_updated = []
        self.hash_algorithm = 'sha256'
        shared_upload_function_osf(self)

        # Verify files exist in OSF
        headers = {'Authorization': 'Bearer {}'.format(OSF_UPLOAD_TEST_USER_TOKEN)}
        for node in requests.get('http://api.osf.io/v2/users/me/nodes', headers=headers).json()['data']:
            if node['attributes']['title'] == 'NewProject':
                node_id = node['id']
                storage_data = requests.get(
                    node['relationships']['files']['links']['related']['href'], headers=headers).json()
                folder_data = requests.get(
                    storage_data['data'][0]['relationships']['files']['links']['related']['href'], headers=headers).json()
                folder_id = folder_data['data'][0]['id']
                file_data = requests.get(
                    folder_data['data'][0]['relationships']['files']['links']['related']['href'], headers=headers).json()
                break
        self.assertEqual(folder_data['links']['meta']['total'], 2)
        self.assertEqual(folder_data['data'][0]['attributes']['name'], 'funnyfunnyimages')
        self.assertEqual(file_data['links']['meta']['total'], 1)
        self.assertEqual(file_data['data'][0]['attributes']['name'],
                         'Screen Shot 2019-07-15 at 3.26.49 PM.png')
        for data in folder_data['data']:
            if data['attributes']['name'] == 'PRESQT_FTS_METADATA.json':
                # Download the content of the metadata file
                metadata = requests.get(data['links']['move'], headers=headers).content
                break

        metadata_dict = json.loads(metadata)
        self.assertEqual(metadata_dict['context']['globus'],
                         'https://docs.globus.org/api/transfer/overview/')
        self.assertEqual(metadata_dict['actions'][0]['actionType'], 'resource_upload')
        self.assertEqual(metadata_dict['actions'][0]['sourceTargetName'], 'Local Machine')
        self.assertEqual(metadata_dict['actions'][0]['destinationTargetName'], 'osf')
        self.assertEqual(metadata_dict['actions'][0]['destinationUsername'], 'Prometheus')
        self.assertEqual(len(metadata_dict['actions'][0]['files']['created']), 1)
        # delete upload folder
        shutil.rmtree(self.ticket_path)

        ######## 202 when uploading to an existing container with duplicate files ignored ########
        self.resource_id = '{}:osfstorage'.format(node_id)
        self.duplicate_action = 'ignore'
        self.url = reverse('resource', kwargs={
                           'target_name': 'osf', 'resource_id': self.resource_id})
        self.file = 'presqt/api_v1/tests/resources/upload/FolderBagItToUpload.zip'
        self.resources_ignored = [
            '/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png']
        self.resources_updated = []
        self.hash_algorithm = 'sha256'
        shared_upload_function_osf(self)

        # # Verify files exist in OSF
        file_data = requests.get(folder_data['data'][0]['relationships']
                                 ['files']['links']['related']['href'], headers=headers).json()
        self.assertEqual(file_data['links']['meta']['total'], 2)
        for file in file_data['data']:
            self.assertIn(file['attributes']['name'], [
                          'Screen Shot 2019-07-15 at 3.26.49 PM.png', 'Screen Shot 2019-07-15 at 3.51.13 PM.png'])
            if file['attributes']['name'] == 'Screen Shot 2019-07-15 at 3.26.49 PM.png':
                original_file_hash = file['attributes']['extra']['hashes']['sha256']

        # Get the updated metadata
        for data in folder_data['data']:
            if data['attributes']['name'] == 'PRESQT_FTS_METADATA.json':
                # Upload link for generating bad metadata test.
                update_url = data['links']['upload']
                # Download the content of the metadata file
                metadata = requests.get(data['links']['move'], headers=headers).content
                break

        metadata_dict = json.loads(metadata)

        # Verify there are multiple actions
        self.assertEqual(len(metadata_dict['actions']), 2)
        # Verify that a file was created and one was ignored
        self.assertEqual(len(metadata_dict['actions'][0]['files']['created']), 1)
        self.assertEqual(metadata_dict['actions'][0]['files']['created'][0]['destinationPath'],
                         'NewProject/osfstorage/funnyfunnyimages/Screen Shot 2019-07-15 at 3.51.13 PM.png')
        self.assertEqual(len(metadata_dict['actions'][0]['files']['ignored']), 1)
        self.assertEqual(metadata_dict['actions'][0]['files']['ignored'][0]['destinationPath'],
                         'NewProject/osfstorage/funnyfunnyimages/Screen Shot 2019-07-15 at 3.26.49 PM.png')

        # Update metadata to be invalid for testing purposes.
        metadata_dict['test_bad_metadata'] = metadata_dict.pop('actions')
        encoded_metadata = json.dumps(metadata_dict, indent=4).encode('utf-8')
        requests.put(update_url, headers=headers,
                     params={'kind': 'file'}, data=encoded_metadata)

        # delete upload folder
        shutil.rmtree(self.ticket_path)

        # ######## 202 when uploading to an existing container with duplicate files replaced ########
        self.resource_id = folder_id
        self.duplicate_action = 'update'
        self.url = reverse('resource', kwargs={
                           'target_name': 'osf', 'resource_id': self.resource_id})
        self.file = 'presqt/api_v1/tests/resources/upload/FolderUpdateBagItToUpload.zip'
        self.resources_ignored = ['/Screen Shot 2019-07-15 at 3.51.13 PM.png']
        self.resources_updated = ['/Screen Shot 2019-07-15 at 3.26.49 PM.png']
        self.hash_algorithm = 'sha256'
        shared_upload_function_osf(self)

        # delete upload folder
        shutil.rmtree(self.ticket_path)

        # Verify files exist in OSF
        file_data = requests.get(folder_data['data'][0]['relationships']
                                 ['files']['links']['related']['href'], headers=headers).json()
        self.assertEqual(file_data['links']['meta']['total'], 2)
        for file in file_data['data']:
            self.assertIn(file['attributes']['name'], [
                          'Screen Shot 2019-07-15 at 3.26.49 PM.png', 'Screen Shot 2019-07-15 at 3.51.13 PM.png'])
            if file['attributes']['name'] == 'Screen Shot 2019-07-15 at 3.26.49 PM.png':
                new_file_hash = file['attributes']['extra']['hashes']['sha256']

        # Updated folder data
        updated_folder_data = requests.get(storage_data['data'][0]['relationships']['files']['links']['related']['href'],
                                           headers=headers).json()
        # Ensure the INVALID_PRESQT_METADATA file exists and is what we expect.
        # Also check that the new metadata file is what we expect.
        for data in updated_folder_data['data']:
            if data['attributes']['name'] == 'INVALID_PRESQT_FTS_METADATA.json':
                invalid_metadata = requests.get(data['links']['move'], headers=headers).content
                invalid_dict = json.loads(invalid_metadata)
            elif data['attributes']['name'] == 'PRESQT_FTS_METADATA.json':
                new_metadata = requests.get(data['links']['move'], headers=headers).content
                new_metadata_dict = json.loads(new_metadata)
        self.assertEqual(invalid_dict, metadata_dict)

        self.assertEqual(new_metadata_dict['context']['globus'],
                         'https://docs.globus.org/api/transfer/overview/')
        self.assertEqual(len(new_metadata_dict['actions']), 1)
        self.assertEqual(len(new_metadata_dict['actions'][0]['files']['created']), 0)
        self.assertEqual(len(new_metadata_dict['actions'][0]['files']['updated']), 1)
        self.assertEqual(len(new_metadata_dict['actions'][0]['files']['ignored']), 1)
        # Make sure the file we have replaced has a different hash than the original
        self.assertNotEqual(original_file_hash, new_file_hash)

        # ######## 202 when uploading to an existing container with mismatched algorithms ########
        self.resource_id = node_id
        self.duplicate_action = 'ignore'
        self.url = reverse('resource', kwargs={
                           'target_name': 'osf', 'resource_id': self.resource_id})
        self.file = 'presqt/api_v1/tests/resources/upload/GoodBagItsha512.zip'
        self.resources_updated = []
        self.resources_ignored = []
        self.hash_algorithm = 'sha256'
        shared_upload_function_osf(self)

        # delete upload folder
        shutil.rmtree(self.ticket_path)

    def test_success_202_large_duplicate_connection_error(self):
        """
        Return a 202 if we upload a large duplicate file. We have a separate test here because
        OSF will return a ConnectionError instead of a 409 when the duplicate file is large enough.
        """
        project_file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.post(url, {'presqt-file': open(project_file, 'rb')}, **self.headers)
        self.assertEqual(response.status_code, 202)

        # Wait for the process to finish
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)
        process_info_path = 'mediafiles/uploads/{}/process_info.json'.format(ticket_number)
        process_info = read_file(process_info_path, True)
        process_wait(process_info, ticket_path)

        # Wait for the process to finish
        process_wait(process_info, ticket_path)

        # delete upload folder
        shutil.rmtree(ticket_path)

        # Get new project ID
        headers = {'Authorization': 'Bearer {}'.format(OSF_UPLOAD_TEST_USER_TOKEN)}
        for node in requests.get('http://api.osf.io/v2/users/me/nodes', headers=headers).json()[
                'data']:
            if node['attributes']['title'] == 'NewProject':
                node_id = node['id']

        # Upload the large file initially
        large_file = 'presqt/api_v1/tests/resources/upload/LargeBagToUpload.zip'
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': node_id})
        response = self.client.post(url, {'presqt-file': open(large_file, 'rb')}, **self.headers)
        self.assertEqual(response.status_code, 202)

        # Wait for the process to finish
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)
        process_info_path = 'mediafiles/uploads/{}/process_info.json'.format(ticket_number)
        process_info = read_file(process_info_path, True)
        process_wait(process_info, ticket_path)

        # Wait for the process to finish
        process_wait(process_info, ticket_path)

        # delete upload folder
        shutil.rmtree(ticket_path)

        # Attempt to upload the same large file and get the duplicate ConnectionError
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': node_id})
        response = self.client.post(url, {'presqt-file': open(large_file, 'rb')}, **self.headers)
        self.assertEqual(response.status_code, 202)

        # Wait for the process to finish
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)
        process_info_path = 'mediafiles/uploads/{}/process_info.json'.format(ticket_number)
        process_info = read_file(process_info_path, True)
        process_wait(process_info, ticket_path)

        # Wait for the process to finish
        process_wait(process_info, ticket_path)

        # delete upload folder
        shutil.rmtree(ticket_path)

    def test_bad_metadata_request(self):
        """
        Ensure that an error is returned if OSF doesn't return a 201 status code.
        """
        self.assertRaises(PresQTError, osf_upload_metadata, self.token, 'eggtest',
                          {"bad": "metadata"})

    def test_error_updating_metadata_file(self):
        """
        Test that an error is raised if there's an issue updating a metadata file.
        """
        # Mock a server error for when a put request is made.
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        self.resource_id = None
        self.duplicate_action = 'ignore'
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.resources_ignored = []
        self.resources_updated = []
        self.hash_algorithm = 'sha256'
        shared_upload_function_osf(self)

        # Verify files exist in OSF
        headers = {'Authorization': 'Bearer {}'.format(OSF_UPLOAD_TEST_USER_TOKEN)}
        for node in requests.get('http://api.osf.io/v2/users/me/nodes', headers=headers).json()['data']:
            if node['attributes']['title'] == 'NewProject':
                node_id = node['id']

        # Now I'll make an explicit call to our metadata function with a mocked server error and ensure
        # it is raising an exception.
        with patch('requests.put') as mock_request:
            mock_request.return_value = mock_req
            # Attempt to update the metadata, but the server is down!
            self.assertRaises(PresQTError, osf_upload_metadata, self.token, node_id,
                              {"context": {}, "actions": []})

        # Delete corresponding folder
        shutil.rmtree(self.ticket_path)

    def test_error_creating_invalid_metadata_file(self):
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
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.resources_ignored = []
        self.resources_updated = []
        self.hash_algorithm = 'sha256'
        shared_upload_function_osf(self)

        # Verify files exist in OSF
        headers = {'Authorization': 'Bearer {}'.format(OSF_UPLOAD_TEST_USER_TOKEN)}
        for node in requests.get('http://api.osf.io/v2/users/me/nodes', headers=headers).json()['data']:
            if node['attributes']['title'] == 'NewProject':
                node_id = node['id']
                storage_data = requests.get(
                    node['relationships']['files']['links']['related']['href'], headers=headers).json()
                folder_data = requests.get(
                    storage_data['data'][0]['relationships']['files']['links']['related']['href'], headers=headers).json()

        # Get the metadata file
        for data in folder_data['data']:
            if data['attributes']['name'] == 'PRESQT_FTS_METADATA.json':
                # Upload link for generating bad metadata test.
                update_url = data['links']['upload']
                # Download the content of the metadata file
                metadata = requests.get(data['links']['move'], headers=headers).content
                break
        metadata_dict = json.loads(metadata)
        # Update metadata to be invalid for testing purposes.
        metadata_dict['test_bad_metadata'] = metadata_dict.pop('actions')
        encoded_metadata = json.dumps(metadata_dict, indent=4).encode('utf-8')
        requests.put(update_url, headers=headers,
                     params={'kind': 'file'}, data=encoded_metadata)

        # Now I'll make an explicit call to our metadata function with a mocked server error and ensure
        # it is raising an exception.
        with patch('requests.post') as mock_request:
            mock_request.return_value = mock_req
            # Attempt to update the metadata, but the server is down!
            self.assertRaises(PresQTError, osf_upload_metadata, self.token, node_id,
                              {"context": {}, "actions": []})

        # Delete corresponding folder
        shutil.rmtree(self.ticket_path)

    def test_proper_message_if_metadata_fails_validation(self):
        """
        """
        self.resource_id = None
        self.duplicate_action = 'ignore'
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        self.resources_ignored = []
        self.resources_updated = []
        self.hash_algorithm = 'sha256'

        with mock.patch('presqt.api_v1.utilities.metadata.upload_metadata.write_and_validate_metadata') as upload_mock:
            upload_mock.return_value = "Whoops"
            self.headers['HTTP_PRESQT_FILE_DUPLICATE_ACTION'] = self.duplicate_action
            response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')},
                                        **self.headers)

            ticket_number = response.data['ticket_number']
            self.ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

            # Verify status code and message
            self.assertEqual(response.status_code, 202)
            self.assertEqual(response.data['message'], 'The server is processing the request.')

            # Verify process_info file status is 'in_progress' initially
            process_info = read_file('{}/process_info.json'.format(self.ticket_path), True)
            self.assertEqual(process_info['status'], 'in_progress')

            # Wait until the spawned off process finishes in the background to do further validation
            while process_info['status'] == 'in_progress':
                try:
                    process_info = read_file('{}/process_info.json'.format(self.ticket_path), True)
                except json.decoder.JSONDecodeError:
                    # Pass while the process_info file is being written to
                    pass
            self.assertEqual(process_info['message'], "Upload successful but with metadata errors.")

        # Delete corresponding folder
        shutil.rmtree(self.ticket_path)
