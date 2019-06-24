import io
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
from presqt.api_v1.utilities import write_file
from presqt.api_v1.utilities.io.read_file import read_file
from presqt.api_v1.utilities.io.remove_path_contents import remove_path_contents
from presqt.api_v1.utilities.multiprocess.watchdog import process_watchdog
from presqt.api_v1.views.resource.resource_download import download_resource
from presqt.fixity import fixity_checker


class TestPrepareDownload(TestCase):
    """
    Test the `api_v1/targets/{target_name}/resources/{resource_id}/download/` endpoint's GET method.
    """
    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': TEST_USER_TOKEN}

    def shared_get_success_function_202(self):
        """
        This function will be used by tests that successfully hit the PrepareDownload endpoint.
        It uses class attributes that are set in the test methods.

        Returns
        -------
        Fixity JSON from the fixity_info.json file
        """
        url = reverse('prepare_download', kwargs={'target_name': self.target_name,
                                                  'resource_id': self.resource_id})
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
        download_resource('osf', 'resource_download', TEST_USER_TOKEN,
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
        This function will be used by tests that successfully hit the PrepareDownload endpoint but
        fail during the download_resource() function.
        It uses class attributes that are set in the test methods.
        """
        url = reverse('prepare_download', kwargs={'target_name': self.target_name,
                                                  'resource_id': self.resource_id})
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
        # 'download_resource' function manually with the same parameters that the multiprocess
        # version ran. And run the same exact checks.

        # First we need to remove the contents of the ticket path except 'process_info.json'
        remove_path_contents(ticket_path, 'process_info.json')
        process_info_path = '{}/process_info.json'.format(ticket_path)
        # Call the download_resource manually
        process_state = multiprocessing.Value('b', 0)
        download_resource('osf', 'resource_download', self.header['HTTP_PRESQT_SOURCE_TOKEN'],
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
        self.file_number = 8
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
        self.file_number = 8
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
        self.file_number = 8
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
        self.file_number = 8
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
        self.file_number = 8
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
        self.file_number = 10
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
        self.file_number = 11
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
        self.file_number = 67
        self.file_name = 'Test Project/osfstorage/Docs/Docs2/Docs3/CODE_OF_CONDUCT.md'
        self.shared_get_success_function_202()

    def test_get_error_400_missing_token_osf(self):
        """
        Return a 400 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('prepare_download', kwargs={'target_name': 'osf', 'resource_id': '3'})
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
        with open('presqt/api_v1/tests/views/targets_test.json') as json_file:
            with patch("builtins.open") as mock_file:
                mock_file.return_value = json_file
                url = reverse(
                    'prepare_download',
                    kwargs={'target_name': 'test', 'resource_id': '5cd98510f244ec001fe5632f'})
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
        url = reverse('prepare_download', kwargs={'target_name': 'bad_name', 'resource_id': '3'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {'error': "'bad_name' is not a valid Target name."})

    def test_get_202_downloadresource_fails_file_id_doesnt_exist_osf(self):
        """
        Return a 202 if the GET method succeeds but the download_resource function fails because
        the file_id given does not map to a resource.
        """
        self.resource_id = '1234'
        self.target_name = 'osf'
        self.status_code = 404
        self.status_message = "Resource with id '1234' not found for this user."
        self.shared_get_success_function_202_with_error()

    def test_get_202_downloadresource_fails_bad_storage_provider_osf(self):
        """
        Return a 202 if the GET method succeeds but the download_resource function fails because
        a bad storage provider name was given in the storage ID
        """
        self.resource_id = 'cmn5z:badstorage'
        self.target_name = 'osf'
        self.status_code = 404
        self.status_message = "Resource with id 'cmn5z:badstorage' not found for this user."
        self.shared_get_success_function_202_with_error()

    def test_get_202_downloadresource_fails_not_authorized_osf(self):
        """
        Return a 200 if the GET method succeeds but the download_resource function fails because
        the user doesn't have access to this resource.
        """
        self.resource_id = 'q5xmw'
        self.target_name = 'osf'
        self.status_code = 403
        self.status_message = "User does not have access to this resource with the token provided."
        self.shared_get_success_function_202_with_error()

    def test_get_202_downloadresource_fails_invalid_token_osf(self):
        """
        Return a 202 if the GET method succeeds but the download_resource function fails because
        the token provided is not a valid token.
        """
        self.resource_id = 'cmn5z'
        self.target_name = 'osf'
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': 'bad_token'}
        self.status_code = 401
        self.status_message = "Token is invalid. Response returned a 401 status code."
        self.shared_get_success_function_202_with_error()

    # Fixity failed!
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
        url = reverse('prepare_download', kwargs={'target_name': 'osf',
                                                  'resource_id': resource_id})
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
        self.assertEqual(len(zip_file.namelist()), 8)

        # Grab the .jpg file in the zip and run it back through the fixity checker with bad hashes
        # So we can get a failed fixity. This fixity variable will be used later in our Patch.
        fixity = fixity_checker(
            read_file('{}/{}/data/22776439564_7edbed7e10_o.jpg'.format(ticket_path, base_name)),
            hashes)

        # Since the coverage package does not pick up the multiprocessing, we will run the
        # 'download_resource' function manually with the same parameters that the multiprocess
        # version ran. And run the same exact checks.

        # First we need to remove the contents of the ticket path except 'process_info.json'
        remove_path_contents(ticket_path, 'process_info.json')
        process_info_path = '{}/process_info.json'.format(ticket_path)

        self.assertEqual(fixity['fixity'], False)

        # Patch the fixity_checker() function to return our bad fixity dictionary.
        with patch('presqt.fixity.fixity_checker') as fake_send:
            # Manually verify the fixity_checker will fail
            fake_send.return_value = fixity
            process_state = multiprocessing.Value('b', 0)
            download_resource('osf', 'resource_download', TEST_USER_TOKEN,
                              resource_id, ticket_path, process_info_path, process_state)

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'finished'
        self.assertEqual(final_process_info['status'], 'finished')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), 8)

        # Verify that the resource we expect is there.
        self.assertEqual(
            os.path.isfile('{}/{}/data/22776439564_7edbed7e10_o.jpg'.format(ticket_path, base_name)), True)

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
        # Start the download_resource process manually
        process_state = multiprocessing.Value('b', 0)
        function_process = multiprocessing.Process(target=download_resource, args=[
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

        # Start the download_resource process manually
        process_state = multiprocessing.Value('b', 0)
        function_process = multiprocessing.Process(target=download_resource, args=[
            'osf', 'resource_download', TEST_USER_TOKEN, resource_id,
            ticket_path, process_info_path, process_state])
        function_process.start()

        # start watchdog function manually
        process_watchdog(function_process, process_info_path, 1, process_state)

        # Make sure the process_watchdog reached a failure and updated the status to 'failed'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'failed')
        self.assertEqual(process_info['message'], 'The process took too long on the server.')

        # Delete corresponding folder
        shutil.rmtree(ticket_path)


class TestDownloadResource(TestCase):
    """
    Test the `api_v1/download/<ticket_id>/` endpoint's GET method.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': TEST_USER_TOKEN}
        self.resource_id = '5cd98510f244ec001fe5632f'

    def call_prepare_download(self):
        #### Call the prepare_download endpoint first to download the resources ####
        self.hashes = {
            "sha256": "3e517cda95ddbfcb270ab273201517f5ae0ee1190a9c5f6f7e6662f97868366f",
            "md5": "9e79fdd9032629743fca52634ecdfd86"
        }

        url = reverse('prepare_download', kwargs={'target_name': 'osf', 'resource_id': self.resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 202)
        self.ticket_number = response.data['ticket_number']

        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(self.ticket_number),
                                 True)
        # Save initial process data that we can use to rewrite to the process_info file for testing
        self.initial_process_info = process_info

        # Wait until the spawned off process finishes in the background
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(
                    'mediafiles/downloads/{}/process_info.json'.format(self.ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass
        self.assertNotEqual(process_info['status'], 'in_progress')

    def test_get_success_200_osf(self):
        """
        Return a 200 along with a zip file of the resource requested.
        """
        self.call_prepare_download()

        url = reverse('download_resource', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename=osf_download_{}.zip'.format(self.resource_id))
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 8)

        # Verify the custom hash_file information is correct
        with zip_file.open('osf_download_{}/data/fixity_info.json'.format(self.resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], True)
            self.assertEqual(zip_json['fixity_details'], 'Source Hash and PresQT Calculated hash matched.')
            self.assertEqual(zip_json['hash_algorithm'], 'sha256')
            self.assertEqual(zip_json['presqt_hash'], self.hashes['sha256'])

        # Run the file through the fixity checker again to make sure it downloaded correctly
        with zip_file.open('osf_download_{}/data/22776439564_7edbed7e10_o.jpg'.format(self.resource_id)) as myfile:
            temp_file = myfile.read()
            fixity = fixity_checker(temp_file, self.hashes)
            self.assertEqual(fixity['fixity'], True)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_get_success_202_osf(self):
        """
        Return a 202 if the resource has no finished being prepared on the server.
        """
        self.call_prepare_download()

        # Update the fixity_info.json to say the resource hasn't finished processing
        write_file('mediafiles/downloads/{}/process_info.json'.format(self.ticket_number), self.initial_process_info, True)

        url = reverse('download_resource', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        # Verify the status code and content
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data, {'message': 'Download is being processed on the server', 'status_code': None})

        # Verify the status of the process_info file is 'in_progress'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(self.ticket_number), True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_get_success_400_osf(self):
        """
        Return a 400 if the 'presqt-source-token' is missing in the headers
        """
        self.call_prepare_download()

        header = {}
        url = reverse('download_resource', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **header)

        # Verify the status code and content
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'],
                         "'presqt-source-token' missing in the request headers.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_get_accepted_401_osf(self):
        """
        Return a 401 if the 'presqt-source-token' provided in the header does not match
        the 'presqt-source-token' in the process_info file.
        """
        self.call_prepare_download()

        url = reverse('download_resource', kwargs={'ticket_number': self.ticket_number})
        headers = {'HTTP_PRESQT_SOURCE_TOKEN': '1234'}
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['error'],
                         "Header 'presqt-source-token' does not match the 'presqt-source-token' "
                         "for this server process.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_get_error_500_401_token_invalid_osf(self):
        """
        Return a 500 if the resource_download() function running on the server gets a 401 error
        """
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': '1234'}
        self.call_prepare_download()

        url = reverse('download_resource', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "Token is invalid. Response returned a 401 status code.",
                          'status_code': 401})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_get_success_500_403_unauthorized_resource_osf(self):
        """
        Return a 500 if the resource_download() function running on the server gets a 403 error
        """
        self.resource_id = 'q5xmw'
        self.call_prepare_download()

        url = reverse('download_resource', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "User does not have access to this resource with the token provided.",
                          'status_code': 403})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_get_success_500_404_resource_not_found_osf(self):
        """
        Return a 500 if the resource_download() function running on the server gets a 404 error
        """
        self.resource_id = 'bad_id'
        self.call_prepare_download()

        url = reverse('download_resource', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "Resource with id 'bad_id' not found for this user.",
                          'status_code': 404})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_get_success_500_410_gone_osf(self):
        """
        Return a 500 if the resource_download() function running on the server gets a 410 error
        """
        self.resource_id = '5cd989c5f8214b00188af9b5'
        self.call_prepare_download()

        url = reverse('download_resource', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "The requested resource is no longer available.",
                          'status_code': 410})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))
