import hashlib
import io
import json
import zipfile
from unittest.mock import patch, mock_open

from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import TEST_USER_TOKEN
from presqt.fixity import fixity_checker


class TestResourceCollection(TestCase):
    """
    Test the 'api_v1/targets/{target_name}/resources/' endpoint's GET method.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': TEST_USER_TOKEN}

    def test_get_success_osf(self):
        """
        Return a 200 if the GET method is successful when grabbing OSF resources.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = self.client.get(url, **self.header)
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))
        # Verify the count of resource objects is what we expect.
        self.assertEqual(69, len(response.data))

    def test_get_error_400_missing_token_osf(self):
        """
        Return a 400 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
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
                url = reverse('resource_collection', kwargs={'target_name': 'test'})
                response = self.client.get(url, **self.header)
                # Verify the error status code and message
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.data,
                    {'error': "'test' does not support the action 'resource_collection'."})


    def test_get_error_401_invalid_token_osf(self):
        """
`       Return a 401 if the token provided is not a valid token.
        """
        client = APIClient()
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'bad_token'}
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        response = client.get(url, **header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "Token is invalid. Response returned a 401 status code."})

    def test_get_error_404_bad_target_name_osf(self):
        """
        Return a 404 if the GET method fails because a bad target_name was given.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'bad_name'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {'error': "'bad_name' is not a valid Target name."})


class TestResource(TestCase):
    """
    Test the `api_v1/targets/{target_name}/resources/{resource_id}/` endpoint's GET method.
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

        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': resource_id})
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
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': resource_id})
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
                                          'resource_id': resource_id})
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
                                          'resource_id': resource_id})
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
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': '3'})
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
                url = reverse('resource', kwargs={'target_name': 'test', 'resource_id': 'cmn5z'})
                response = self.client.get(url, **self.header)
                # Verify the error status code and message
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.data,
                    {'error': "'test' does not support the action 'resource_detail'."})

    def test_get_error_401_invalid_token_osf(self):
        """
`       Return a 401 if the token provided is not a valid token.
        """
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'bad_token'}
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'cmn5z'})
        response = self.client.get(url, **header)

        # Verify the error status code and message
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "Token is invalid. Response returned a 401 status code."})

    def test_get_error_403_not_authorized_osf(self):
        """
        Return a 403 if the GET method fails because the user doesn't have access to this resource.
        """
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'q5xmw'})
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
        url = reverse('resource', kwargs={'target_name': 'bad_name', 'resource_id': '3'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {'error': "'bad_name' is not a valid Target name."})

    def test_get_error_404_file_id_doesnt_exist_osf(self):
        """
        Return a 404 if the GET method fails because the file_id given does not map to a resource.
        """
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': '1234'})
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
        url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'cmn5z:badstorage'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data,
                         {'error': "Resource with id 'cmn5z:badstorage' not found for this user."})


class TestResourceDownload(TestCase):
    """
    Test the `api_v1/targets/{target_name}/resources/{resource_id}/download/` endpoint's GET method.
    """
    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': TEST_USER_TOKEN}

    def test_get_success_200_file_osfstorage_file_jpg_osf(self):
        """
        Return a 200 if the GET method is successful when downloading
        OSF resources file of type '.jpg'.
        """
        hashes = {
            "sha256": "3e517cda95ddbfcb270ab273201517f5ae0ee1190a9c5f6f7e6662f97868366f",
            "md5": "9e79fdd9032629743fca52634ecdfd86"
        }
        resource_id = '5cd98510f244ec001fe5632f'

        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))

        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename=osf_download_{}.zip'.format(resource_id))
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 8)
        # Verify the custom hash_file information is correct
        with zip_file.open('mediafiles/osf_download_5cd98510f244ec001fe5632f/data/fixity_info.json') as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], True)
            self.assertEqual(zip_json['fixity_details'], 'Source Hash and PresQT Calculated hash matched.')
            self.assertEqual(zip_json['hash_algorithm'], 'sha256')
            self.assertEqual(zip_json['presqt_hash'], hashes['sha256'])

        # Run the file through the fixity checker again to make sure it downloaded correctly
        with zip_file.open('mediafiles/osf_download_5cd98510f244ec001fe5632f/data/22776439564_7edbed7e10_o.jpg') as myfile:
            temp_file = myfile.read()
            fixity = fixity_checker(temp_file, hashes)
            self.assertEqual(fixity['fixity'], True)

    def test_get_success_200_file_osfstorage_file_docx_osf(self):
        """
        Return a 200 if the GET method is successful when downloading
        OSF resources file of type '.docx'.
        """
        hashes = {
            "sha256": "f87040f7f12957c996d0440ebadeca9e55908092faea2f600dc4b079f75ea943",
            "md5": "38b6bd925c04af35a10cacf00704a2a4"
        }
        resource_id = '5cd9831c054f5b001a5ca2af'

        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))

        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename=osf_download_{}.zip'.format(resource_id))
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 8)
        # Verify the custom hash_file information is correct
        with zip_file.open('mediafiles/osf_download_5cd9831c054f5b001a5ca2af/data/fixity_info.json') as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], True)
            self.assertEqual(zip_json['fixity_details'], 'Source Hash and PresQT Calculated hash matched.')
            self.assertEqual(zip_json['hash_algorithm'], 'sha256')
            self.assertEqual(zip_json['presqt_hash'], hashes['sha256'])

        # Run the file through the fixity checker again to make sure it downloaded correctly
        with zip_file.open('mediafiles/osf_download_5cd9831c054f5b001a5ca2af/data/2017-01-27 PresQT Workshop Planning Meeting Items.docx') as myfile:
            temp_file = myfile.read()
            fixity = fixity_checker(temp_file, hashes)
            self.assertEqual(fixity['fixity'], True)

    def test_get_success_200_file_osfstorage_file_js_osf(self):
        """
        Return a 200 if the GET method is successful when downloading
        OSF resources file of type '.js'.
        """
        hashes = {
            "sha256": "a64091e8b8f3659184a4d4ba13adca36347aa8b981ee6c672bd2bd3a014c5a0c",
            "md5": "1f67b72a90b524873a26cd5d2671d0ef"
        }
        resource_id = '5cd98978054f5b001a5ca746'

        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))

        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename=osf_download_{}.zip'.format(resource_id))
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 8)
        # Verify the custom hash_file information is correct
        with zip_file.open('mediafiles/osf_download_5cd98978054f5b001a5ca746/data/fixity_info.json') as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], True)
            self.assertEqual(zip_json['fixity_details'], 'Source Hash and PresQT Calculated hash matched.')
            self.assertEqual(zip_json['hash_algorithm'], 'sha256')
            self.assertEqual(zip_json['presqt_hash'], hashes['sha256'])

        # Run the file through the fixity checker again to make sure it downloaded correctly
        with zip_file.open('mediafiles/osf_download_5cd98978054f5b001a5ca746/data/build-plugins.js') as myfile:
            temp_file = myfile.read()
            fixity = fixity_checker(temp_file, hashes)
            self.assertEqual(fixity['fixity'], True)

    def test_get_success_200_file_osfstorage_file_pdf_osf(self):
        """
        Return a 200 if the GET method is successful when downloading
        OSF resources file of type '.pdf'.
        """
        hashes = {
            "sha256": "343e249fdb0818a58edcc64663e1eb116843b4e1c4e74790ff331628593c02be",
            "md5": "a4536efb47b26eaf509edfdaca442037"
        }
        resource_id = '5cd98978f244ec001ee86609'

        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))

        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename=osf_download_{}.zip'.format(resource_id))
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 8)
        # Verify the custom hash_file information is correct
        with zip_file.open('mediafiles/osf_download_5cd98978f244ec001ee86609/data/fixity_info.json') as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], True)
            self.assertEqual(zip_json['fixity_details'], 'Source Hash and PresQT Calculated hash matched.')
            self.assertEqual(zip_json['hash_algorithm'], 'sha256')
            self.assertEqual(zip_json['presqt_hash'], hashes['sha256'])

        # Run the file through the fixity checker again to make sure it downloaded correctly
        with zip_file.open('mediafiles/osf_download_5cd98978f244ec001ee86609/data/Character Sheet - Alternative - Print Version.pdf') as myfile:
            temp_file = myfile.read()
            fixity = fixity_checker(temp_file, hashes)
            self.assertEqual(fixity['fixity'], True)

    def test_get_success_200_file_osfstorage_file_mp3_osf(self):
        """
        Return a 200 if the GET method is successful when downloading
        OSF resources file of type '.mp3'.
        """
        hashes = {
            "sha256": "fe3e904fbd549a3ac014bc26fb3d5042d58759f639f24e745dba3580ea316850",
            "md5": "845248e5456033c6df85b5cffcd7ea8a"
        }
        resource_id = '5cd98979f8214b00198b1153'

        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))

        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename=osf_download_{}.zip'.format(resource_id))
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 8)
        # Verify the custom hash_file information is correct
        with zip_file.open('mediafiles/osf_download_5cd98979f8214b00198b1153/data/fixity_info.json') as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], True)
            self.assertEqual(zip_json['fixity_details'], 'Source Hash and PresQT Calculated hash matched.')
            self.assertEqual(zip_json['hash_algorithm'], 'sha256')
            self.assertEqual(zip_json['presqt_hash'], hashes['sha256'])

        # Run the file through the fixity checker again to make sure it downloaded correctly
        with zip_file.open('mediafiles/osf_download_5cd98979f8214b00198b1153/data/02 - The Widow.mp3') as myfile:
            temp_file = myfile.read()
            fixity = fixity_checker(temp_file, hashes)
            self.assertEqual(fixity['fixity'], True)

    def test_200_success_no_hash_google_drive_osf(self):
        """
        Return a 200 if the GET method is successful when downloading
        OSF resources file of type '.mp3'.
        """
        resource_id = '5cd98a30f2c01100177156be'
        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))

        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename=osf_download_{}.zip'.format(resource_id))
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 8)
        # Verify the custom hash_file information is correct
        with zip_file.open('mediafiles/osf_download_5cd98a30f2c01100177156be/data/fixity_info.json') as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], None)
            self.assertEqual(zip_json['fixity_details'], 'Either a Source Hash was not provided or the source hash algorithm is not supported.')
            self.assertEqual(zip_json['hash_algorithm'], 'md5')
            self.assertEqual(zip_json['source_hash'], None)
            presqt_hash = zip_json['presqt_hash']

        with zip_file.open('mediafiles/osf_download_5cd98a30f2c01100177156be/data/Character Sheet - Alternative - Print Version.pdf') as myfile:
            temp_file = myfile.read()
            h = hashlib.md5(temp_file)
            hash_hex = h.hexdigest()
            # Verify the downloaded file in the zip matched the provided provided presqt hash
            self.assertEqual(presqt_hash, hash_hex)

    def test_get_success_200_folder_osf(self):
        """
        Return a 200 if the GET method is successful when downloading OSF resource folder.
        """
        resource_id = '5cd98b0af244ec0021e5f8dd'
        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename=osf_download_{}.zip'.format(resource_id))
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 10)
        # Verify a certain file path exists in the zip file
        self.assertIn('mediafiles/osf_download_5cd98b0af244ec0021e5f8dd/data/Docs2/Docs3/CODE_OF_CONDUCT.md', zip_file.namelist())
        # Verify the custom hash_file information is correct
        with zip_file.open('mediafiles/osf_download_5cd98b0af244ec0021e5f8dd/data/fixity_info.json') as fixityfile:
            zip_json = json.load(fixityfile)
            for fixity_dict in zip_json:
                self.assertEqual(fixity_dict['fixity'], True)


    def test_get_success_200_storage_googledrive_osf(self):
        """
        Return a 200 if the GET method is successful when downloading OSF resource Google Drive storage.
        """
        resource_id = 'cmn5z:googledrive'
        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename=osf_download_{}.zip'.format(resource_id))
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 11)
        # Verify a certain file path exists in the zip file
        self.assertIn(
            'mediafiles/osf_download_cmn5z:googledrive/data/googledrive/Google Images/IMG_4740.jpg',
            zip_file.namelist())
        # Verify the custom hash_file information is correct
        with zip_file.open(
                'mediafiles/osf_download_cmn5z:googledrive/data/fixity_info.json') as fixityfile:
            zip_json = json.load(fixityfile)
            for fixity_dict in zip_json:
                self.assertEqual(fixity_dict['fixity'], None)


    def test_200_success_fixity_failed_osf(self):
        """
        Since both the file and hashes are coming from OSF API calls we don't have the opportunity
            to corrupt the file or change the expected hashes before running the fixity checker.
            To solve this the test will have two parts:
            1. The first part will be verifying that the fixity checker function will throw an
                error if given a file and a mismatched hash dictionary.
            2. The second will do another GET request but this time take the returned fixity
                dictionary for a failed fixity check and force fixity_checker() to return the
                failed fixity dictionary.
        """
        hashes = {
            "sha256": "bad_hash",
            "md5": "bad_hash"
        }
        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': '5cd98510f244ec001fe5632f'})
        response = self.client.get(url, **self.header)
        # Manually verify the fixity_checker will fail
        fixity = fixity_checker(response.content, hashes)
        self.assertEqual(fixity['fixity'], False)

        # Use the returned 'fixity' object from the failed fixity check and have
        # fixity_check() force return that when making the same GET request as above.
        with patch('presqt.fixity.fixity_checker') as fake_send:
            fake_send.return_value = fixity
            response = self.client.get(url, **self.header)
            zip_file = zipfile.ZipFile(io.BytesIO(response.content))
            self.assertEqual(response.status_code, 200)
            with zip_file.open('mediafiles/osf_download_5cd98510f244ec001fe5632f/data/fixity_info.json') as fixityfile:
                zip_json = json.load(fixityfile)[0]
                self.assertEqual(zip_json['fixity'], False)
                self.assertEqual(zip_json['fixity_details'], 'Source Hash and PresQT Calculated hash do not match.')
                self.assertNotEqual(zip_json['source_hash'], zip_json['presqt_hash'])

    def test_get_error_400_missing_token_osf(self):
        """
        Return a 400 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('resource_download', kwargs={'target_name': 'osf', 'resource_id': '3'})
        response = self.client.get(url)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "'presqt-source-token' missing in the request headers."})
#
    def test_get_error_400_target_not_supported_test_target(self):
        """
        Return a 400 if the GET method fails because the target requested does not support
        this endpoint's action.
        """
        with open('presqt/api_v1/tests/views/targets_test.json') as json_file:
            with patch("builtins.open") as mock_file:
                mock_file.return_value = json_file
                url = reverse(
                    'resource_download',
                    kwargs={'target_name': 'test', 'resource_id': '5cd98510f244ec001fe5632f'})
                response = self.client.get(url, **self.header)
                # Verify the error status code and message
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.data,
                    {'error': "'test' does not support the action 'resource_download'."})
#
    def test_get_error_401_invalid_token_osf(self):
        """
`       Return a 401 if the token provided is not a valid token.
        """
        client = APIClient()
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'bad_token'}
        url = reverse('resource_download', kwargs={'target_name': 'osf', 'resource_id': 'cmn5z'})
        response = client.get(url, **header)

        # Verify the error status code and message
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "Token is invalid. Response returned a 401 status code."})
#
    def test_get_error_403_not_authorized_osf(self):
        """
        Return a 403 if the GET method fails because the user doesn't have access to this resource.
        """
        url = reverse('resource_download', kwargs={'target_name': 'osf', 'resource_id': 'q5xmw'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data,
            {'error': "User does not have access to this resource with the token provided."})
#
#
    def test_get_error_404_bad_target_name_osf(self):
        """
        Return a 404 if the GET method fails because a bad target_name was given.
        """
        url = reverse('resource_download', kwargs={'target_name': 'bad_name', 'resource_id': '3'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {'error': "'bad_name' is not a valid Target name."})
#
    def test_get_error_404_file_id_doesnt_exist_osf(self):
        """
        Return a 404 if the GET method fails because the file_id given does not map to a resource.
        """
        url = reverse('resource_download', kwargs={'target_name': 'osf', 'resource_id': '1234'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data,
                         {'error': "Resource with id '1234' not found for this user."})
#
    def test_get_error_404_bad_storage_provider_osf(self):
        """
        Return a 404 if the GET method fails because a bad storage provider name was given in the
        storage ID
        """
        url = reverse('resource_download',
                      kwargs={'target_name': 'osf', 'resource_id': 'cmn5z:badstorage'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data,
                         {'error': "Resource with id 'cmn5z:badstorage' not found for this user."})
