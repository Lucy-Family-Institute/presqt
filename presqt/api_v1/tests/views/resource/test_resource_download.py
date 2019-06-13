import json
import os
import shutil
import zipfile
from unittest.mock import patch

from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import TEST_USER_TOKEN
from presqt.api_v1.utilities.io.read_file import read_file
from presqt.api_v1.views.resource.resource_download import download_resource


class TestPrepareDownload(TestCase):
    """
    Test the `api_v1/targets/{target_name}/resources/{resource_id}/download/` endpoint's GET method.
    """
    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': TEST_USER_TOKEN}

    def test_get_success_202_file_osfstorage_jpg_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF
        resource file of type '.jpg'.
        """
        hashes = {
            "sha256": "3e517cda95ddbfcb270ab273201517f5ae0ee1190a9c5f6f7e6662f97868366f",
            "md5": "9e79fdd9032629743fca52634ecdfd86"
        }
        resource_id = '5cd98510f244ec001fe5632f'
        url = reverse('prepare_download', kwargs={'target_name': 'osf', 'resource_id': resource_id})
        response = self.client.get(url, **self.header)

        # Verify the Status Code
        self.assertEqual(response.status_code, 202)
        # Verify response content
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
        self.assertEqual(process_info['status'],'in_progress')

        # Wait until the process finishes to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'finishes'
        self.assertEqual(final_process_info['status'], 'finished')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), 8)

        # Verify that the resource we expect is there.
        self.assertEqual(os.path.isfile('{}/{}/data/22776439564_7edbed7e10_o.jpg'.format(ticket_path, base_name)), True)

        # Verify the custom hash_file information is correct.
        with zip_file.open('{}/data/fixity_info.json'.format(base_name)) as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], True)
            self.assertEqual(zip_json['fixity_details'], 'Source Hash and PresQT Calculated hash matched.')
            self.assertEqual(zip_json['hash_algorithm'], 'sha256')
            self.assertEqual(zip_json['presqt_hash'], hashes['sha256'])

        # Delete corresponding folder
        shutil.rmtree(ticket_path)


    def test_get_success_202_file_osfstorage_docx_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF
        resource file of type '.docx'.
        """
        hashes = {
            "sha256": "f87040f7f12957c996d0440ebadeca9e55908092faea2f600dc4b079f75ea943",
            "md5": "38b6bd925c04af35a10cacf00704a2a4"
        }
        resource_id = '5cd9831c054f5b001a5ca2af'
        url = reverse('prepare_download', kwargs={'target_name': 'osf', 'resource_id': resource_id})
        response = self.client.get(url, **self.header)

        # Verify the Status Code
        self.assertEqual(response.status_code, 202)
        # Verify response content
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the process finishes to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(
                    'mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'finishes'
        self.assertEqual(final_process_info['status'], 'finished')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), 8)

        # Verify that the resource we expect is there.
        self.assertEqual(os.path.isfile('{}/{}/data/2017-01-27 PresQT Workshop Planning Meeting Items.docx'.format(ticket_path, base_name)), True)

        # Verify the custom hash_file information is correct.
        with zip_file.open('{}/data/fixity_info.json'.format(base_name)) as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], True)
            self.assertEqual(zip_json['fixity_details'], 'Source Hash and PresQT Calculated hash matched.')
            self.assertEqual(zip_json['hash_algorithm'], 'sha256')
            self.assertEqual(zip_json['presqt_hash'], hashes['sha256'])

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_get_success_202_file_osfstorage_js_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF
        resource file of type '.js'.
        """
        hashes = {
            "sha256": "a64091e8b8f3659184a4d4ba13adca36347aa8b981ee6c672bd2bd3a014c5a0c",
            "md5": "1f67b72a90b524873a26cd5d2671d0ef"
        }
        resource_id = '5cd98978054f5b001a5ca746'
        url = reverse('prepare_download', kwargs={'target_name': 'osf', 'resource_id': resource_id})
        response = self.client.get(url, **self.header)

        # Verify the Status Code
        self.assertEqual(response.status_code, 202)
        # Verify response content
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the process finishes to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(
                    'mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'finishes'
        self.assertEqual(final_process_info['status'], 'finished')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), 8)

        # Verify that the resource we expect is there.
        self.assertEqual(os.path.isfile('{}/{}/data/build-plugins.js'.format(ticket_path, base_name)), True)

        # Verify the custom hash_file information is correct.
        with zip_file.open('{}/data/fixity_info.json'.format(base_name)) as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], True)
            self.assertEqual(zip_json['fixity_details'], 'Source Hash and PresQT Calculated hash matched.')
            self.assertEqual(zip_json['hash_algorithm'], 'sha256')
            self.assertEqual(zip_json['presqt_hash'], hashes['sha256'])

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_get_success_202_file_osfstorage_pdf_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF
        resource file of type '.pdf'.
        """
        hashes = {
            "sha256": "343e249fdb0818a58edcc64663e1eb116843b4e1c4e74790ff331628593c02be",
            "md5": "a4536efb47b26eaf509edfdaca442037"
        }
        resource_id = '5cd98978f244ec001ee86609'
        url = reverse('prepare_download', kwargs={'target_name': 'osf', 'resource_id': resource_id})
        response = self.client.get(url, **self.header)

        # Verify the Status Code
        self.assertEqual(response.status_code, 202)
        # Verify response content
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the process finishes to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(
                    'mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'finishes'
        self.assertEqual(final_process_info['status'], 'finished')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), 8)

        # Verify that the resource we expect is there.
        self.assertEqual(os.path.isfile('{}/{}/data/Character Sheet - Alternative - Print Version.pdf'.format(ticket_path, base_name)), True)

        # Verify the custom hash_file information is correct.
        with zip_file.open('{}/data/fixity_info.json'.format(base_name)) as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], True)
            self.assertEqual(zip_json['fixity_details'], 'Source Hash and PresQT Calculated hash matched.')
            self.assertEqual(zip_json['hash_algorithm'], 'sha256')
            self.assertEqual(zip_json['presqt_hash'], hashes['sha256'])

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_get_success_202_file_osfstorage_mp3_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF
        resource file of type '.mp3'.
        """
        hashes = {
            "sha256": "fe3e904fbd549a3ac014bc26fb3d5042d58759f639f24e745dba3580ea316850",
            "md5": "845248e5456033c6df85b5cffcd7ea8a"
        }
        resource_id = '5cd98979f8214b00198b1153'
        url = reverse('prepare_download', kwargs={'target_name': 'osf', 'resource_id': resource_id})
        response = self.client.get(url, **self.header)

        # Verify the Status Code
        self.assertEqual(response.status_code, 202)
        # Verify response content
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the process finishes to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(
                    'mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'finishes'
        self.assertEqual(final_process_info['status'], 'finished')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), 8)

        # Verify that the resource we expect is there.
        self.assertEqual(os.path.isfile('{}/{}/data/02 - The Widow.mp3'.format(ticket_path, base_name)), True)

        # Verify the custom hash_file information is correct.
        with zip_file.open('{}/data/fixity_info.json'.format(base_name)) as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], True)
            self.assertEqual(zip_json['fixity_details'], 'Source Hash and PresQT Calculated hash matched.')
            self.assertEqual(zip_json['hash_algorithm'], 'sha256')
            self.assertEqual(zip_json['presqt_hash'], hashes['sha256'])

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_get_success_202_file_googledrive_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF resource
        from a storage provider with no hashes.
        """
        resource_id = '5cd98a30f2c01100177156be'
        url = reverse('prepare_download', kwargs={'target_name': 'osf', 'resource_id': resource_id})
        response = self.client.get(url, **self.header)

        # Verify the Status Code
        self.assertEqual(response.status_code, 202)
        # Verify response content
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the process finishes to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(
                    'mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'finishes'
        self.assertEqual(final_process_info['status'], 'finished')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), 8)

        # Verify that the resource we expect is there.
        self.assertEqual(os.path.isfile('{}/{}/data/Character Sheet - Alternative - Print Version.pdf'.format(ticket_path, base_name)), True)

        # Verify the custom hash_file information is correct.
        with zip_file.open('{}/data/fixity_info.json'.format(base_name)) as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], None)
            self.assertEqual(zip_json['fixity_details'], 'Either a Source Hash was not provided or the source hash algorithm is not supported.')
            self.assertEqual(zip_json['hash_algorithm'], 'md5')
            self.assertEqual(zip_json['source_hash'], None)

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_get_success_202_folder_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF resource folder
        """
        resource_id = '5cd98b0af244ec0021e5f8dd'
        url = reverse('prepare_download', kwargs={'target_name': 'osf', 'resource_id': resource_id})
        response = self.client.get(url, **self.header)

        # Verify the Status Code
        self.assertEqual(response.status_code, 202)
        # Verify response content
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the process finishes to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(
                    'mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'finishes'
        self.assertEqual(final_process_info['status'], 'finished')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), 10)

        # Verify that the resource we expect is there.
        self.assertEqual(os.path.isfile('{}/{}/data/Docs2/Docs3/CODE_OF_CONDUCT.md'.format(ticket_path, base_name)), True)

        # Verify the custom hash_file information is correct.
        with zip_file.open('{}/data/fixity_info.json'.format(base_name)) as fixityfile:
            for zjson in json.load(fixityfile):
                self.assertEqual(zjson['fixity'], True)

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_get_success_202_storage_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF resource storage
        """
        resource_id = 'cmn5z:googledrive'
        url = reverse('prepare_download', kwargs={'target_name': 'osf', 'resource_id': resource_id})
        response = self.client.get(url, **self.header)

        # Verify the Status Code
        self.assertEqual(response.status_code, 202)
        # Verify response content
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the process finishes to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(
                    'mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'finishes'
        self.assertEqual(final_process_info['status'], 'finished')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), 11)

        # Verify that the resource we expect is there.
        self.assertEqual(os.path.isfile('{}/{}/data/googledrive/Google Images/IMG_4740.jpg'.format(ticket_path, base_name)), True)

        # Verify the custom hash_file information is correct.
        with zip_file.open('{}/data/fixity_info.json'.format(base_name)) as fixityfile:
            for zjson in json.load(fixityfile):
                self.assertEqual(zjson['fixity'], None)

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_get_success_202_project_osf(self):
        """
        Return a 202 if the GET method is successful when preparing a download OSF resource project
        """
        resource_id = 'cmn5z'
        url = reverse('prepare_download', kwargs={'target_name': 'osf', 'resource_id': resource_id})
        response = self.client.get(url, **self.header)

        # Verify the Status Code
        self.assertEqual(response.status_code, 202)
        # Verify response content
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the process finishes to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(
                    'mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'finishes'
        self.assertEqual(final_process_info['status'], 'finished')
        # Verify zip file exists and has the proper amount of resources in it.
        base_name = 'osf_download_{}'.format(resource_id)
        zip_path = '{}/{}.zip'.format(ticket_path, base_name)
        zip_file = zipfile.ZipFile(zip_path)
        self.assertEqual(os.path.isfile(zip_path), True)
        self.assertEqual(len(zip_file.namelist()), 67)

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    # Fixity failed!

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
        url = reverse('prepare_download', kwargs={'target_name': 'osf', 'resource_id': '1234'})
        response = self.client.get(url, **self.header)

        # Verify the Status Code
        self.assertEqual(response.status_code, 202)
        # Verify response content
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the process finishes to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(
                    'mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'failed'
        self.assertEqual(final_process_info['status'], 'failed')
        self.assertEqual(final_process_info['message'], "Resource with id '1234' not found for this user.")

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_get_202_downloadresource_fails_bad_storage_provider_osf(self):
        """
        Return a 202 if the GET method succeeds but the download_resource function fails because
        a bad storage provider name was given in the
        storage ID
        """
        url = reverse('prepare_download',
                      kwargs={'target_name': 'osf', 'resource_id': 'cmn5z:badstorage'})
        response = self.client.get(url, **self.header)

        # Verify the Status Code
        self.assertEqual(response.status_code, 202)
        # Verify response content
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the process finishes to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(
                    'mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'failed'
        self.assertEqual(final_process_info['status'], 'failed')
        self.assertEqual(final_process_info['message'],
                         "Resource with id 'cmn5z:badstorage' not found for this user.")

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_get_202_downloadresource_fails_invalid_token_osf(self):
        """
        Return a 202 if the GET method succeeds but the download_resource function fails because
        the token provided is not a valid token.
        """
        client = APIClient()
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'bad_token'}
        url = reverse('prepare_download', kwargs={'target_name': 'osf', 'resource_id': 'cmn5z'})
        response = client.get(url, **header)

        # Verify the Status Code
        self.assertEqual(response.status_code, 202)
        # Verify response content
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the process finishes to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(
                    'mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'failed'
        self.assertEqual(final_process_info['status'], 'failed')
        self.assertEqual(final_process_info['message'],
                         "Token is invalid. Response returned a 401 status code.")

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_get_202_downloadresource_fails_not_authorized_osf(self):
        """
        Return a 200 if the GET method succeeds but the download_resource function fails because
        the user doesn't have access to this resource.
        """
        url = reverse('prepare_download', kwargs={'target_name': 'osf', 'resource_id': 'q5xmw'})
        response = self.client.get(url, **self.header)

        # Verify the Status Code
        self.assertEqual(response.status_code, 202)
        # Verify response content
        self.assertEqual(response.data['message'], 'The server is processing the request.')
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Verify process_info file status is 'in_progress'
        process_info = read_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number),
                                 True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the process finishes to do validation on the resulting files
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(
                    'mediafiles/downloads/{}/process_info.json'.format(ticket_number), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        final_process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        # Verify the final status in the process_info file is 'failed'
        self.assertEqual(final_process_info['status'], 'failed')
        self.assertEqual(final_process_info['message'],
                         "User does not have access to this resource with the token provided.")

        # Delete corresponding folder
        shutil.rmtree(ticket_path)