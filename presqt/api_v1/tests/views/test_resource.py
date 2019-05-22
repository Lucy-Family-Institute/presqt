import hashlib
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
        self.assertEqual(70, len(response.data))

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

    def test_get_success_200_file_osfstorage_osf_jpg(self):
        """
        Return a 200 if the GET method is successful when downloading OSF resources of type '.jpg'.
        """
        hashes = {
            "sha256": "3e517cda95ddbfcb270ab273201517f5ae0ee1190a9c5f6f7e6662f97868366f",
            "md5": "9e79fdd9032629743fca52634ecdfd86"
        }

        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': '5cd98510f244ec001fe5632f'})
        response = self.client.get(url, **self.header)

        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the name
        self.assertEqual(
            response._headers['content-disposition'][1],
            'attachment; filename=22776439564_7edbed7e10_o.jpg')
        # Verify the calculated hash is the same as the matching hash in the defined
        # hashes dictionary.
        self.assertEqual(
            hashes[response._headers['presqt_hash_algorithm'][1]],
            response._headers['presqt_calculated_hash'][1])
        # Verify the given and calculated hashes in the headers match
        self.assertEqual(
            response._headers['presqt_calculated_hash'][1],
            response._headers['presqt_given_hash'][1])
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/octet-stream')
        # Verify the content length
        self.assertEqual(response._headers['content-length'][1], '1728998')
        # Verify that fixity was true
        self.assertEqual(response._headers['presqt_fixity'][1], 'True')

        # Run the file downloaded from the fixity checker to check if the
        # file we got from the response is the same that we sent.
        fixity = fixity_checker(response.content, hashes)
        self.assertEqual(fixity['fixity'], True)


    def test_get_success_200_file_osfstorage_osf_docx(self):
        """
        Return a 200 if the GET method is successful when downloading OSF resources of type '.docx'.
        """
        hashes ={
            "sha256": "f87040f7f12957c996d0440ebadeca9e55908092faea2f600dc4b079f75ea943",
            "md5": "38b6bd925c04af35a10cacf00704a2a4"
        }

        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': '5cd9831c054f5b001a5ca2af'})
        response = self.client.get(url, **self.header)
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the name
        self.assertEqual(
            response._headers['content-disposition'][1],
            'attachment; filename=2017-01-27 PresQT Workshop Planning Meeting Items.docx')
        # Verify the calculated hash is the same as the matching hash in the defined
        # hashes dictionary.
        self.assertEqual(
            hashes[response._headers['presqt_hash_algorithm'][1]],
            response._headers['presqt_calculated_hash'][1])
        # Verify the given and calculated hashes in the headers match
        self.assertEqual(
            response._headers['presqt_calculated_hash'][1],
            response._headers['presqt_given_hash'][1])
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/octet-stream')
        # Verify the content length
        self.assertEqual(response._headers['content-length'][1], '8289')
        # Verify the fixity was true
        self.assertEqual(response._headers['presqt_fixity'][1], 'True')
        # Run the file downloaded from the fixity checker to check if the
        # file we got from teh response is the same that we sent.
        fixity = fixity_checker(response.content, hashes)
        self.assertEqual(fixity['fixity'], True)

    def test_get_success_200_file_osfstorage_osf_js(self):
        """
        Return a 200 if the GET method is successful when downloading OSF resources of type '.js'.
        """
        hashes = {
            "sha256": "a64091e8b8f3659184a4d4ba13adca36347aa8b981ee6c672bd2bd3a014c5a0c",
            "md5": "1f67b72a90b524873a26cd5d2671d0ef"
        }

        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': '5cd98978054f5b001a5ca746'})
        response = self.client.get(url, **self.header)
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the name
        self.assertEqual(
            response._headers['content-disposition'][1],
            'attachment; filename=build-plugins.js')
        # Verify the calculated hash is the same as the matching hash in the defined
        # hashes dictionary.
        self.assertEqual(
            hashes[response._headers['presqt_hash_algorithm'][1]],
            response._headers['presqt_calculated_hash'][1])
        # Verify the given and calculated hashes in the headers match
        self.assertEqual(
            response._headers['presqt_calculated_hash'][1],
            response._headers['presqt_given_hash'][1])
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/octet-stream')
        # Verify the content length
        self.assertEqual(response._headers['content-length'][1], '2507')
        # Verify the fixity was true
        self.assertEqual(response._headers['presqt_fixity'][1], 'True')
        # Run the file downloaded from the fixity checker to check if the
        # file we got from teh response is the same that we sent.
        fixity = fixity_checker(response.content, hashes)
        self.assertEqual(fixity['fixity'], True)

    def test_get_success_200_file_osfstorage_osf_pdf(self):
        """
        Return a 200 if the GET method is successful when downloading OSF resources of type '.pdf'.
        """
        hashes = {
            "sha256": "343e249fdb0818a58edcc64663e1eb116843b4e1c4e74790ff331628593c02be",
            "md5": "a4536efb47b26eaf509edfdaca442037"
        }

        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': '5cd98978f244ec001ee86609'})
        response = self.client.get(url, **self.header)
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the name
        self.assertEqual(
            response._headers['content-disposition'][1],
            'attachment; filename=Character Sheet - Alternative - Print Version.pdf')
        # Verify the calculated hash is the same as the matching hash in the defined
        # hashes dictionary.
        self.assertEqual(
            hashes[response._headers['presqt_hash_algorithm'][1]],
            response._headers['presqt_calculated_hash'][1])
        # Verify the given and calculated hashes in the headers match
        self.assertEqual(
            response._headers['presqt_calculated_hash'][1],
            response._headers['presqt_given_hash'][1])
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/octet-stream')
        # Verify the content length
        self.assertEqual(response._headers['content-length'][1], '146824')
        # Verify the fixity was true
        self.assertEqual(response._headers['presqt_fixity'][1], 'True')
        # Run the file downloaded from the fixity checker to check if the
        # file we got from teh response is the same that we sent.
        fixity = fixity_checker(response.content, hashes)
        self.assertEqual(fixity['fixity'], True)

    def test_get_success_200_file_osfstorage_osf_mp4(self):
        """
        Return a 200 if the GET method is successful when downloading OSF resources of type '.mp4'.
        """
        hashes = {
            "sha256": "7d0ebb2f04bb6a43bda6a918ff2279db0a38afc10b82d21365c41fa9cd203c81",
            "md5": "f2184329b0f75edb39f559effd16f44f"
        }

        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': '5cd989c5f8214b00188af9b5'})
        response = self.client.get(url, **self.header)
        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the name
        self.assertEqual(
            response._headers['content-disposition'][1],
            'attachment; filename=VID_20180314_155531.mp4')
        # Verify the calculated hash is the same as the matching hash in the defined
        # hashes dictionary.
        self.assertEqual(
            hashes[response._headers['presqt_hash_algorithm'][1]],
            response._headers['presqt_calculated_hash'][1])
        # Verify the given and calculated hashes in the headers match
        self.assertEqual(
            response._headers['presqt_calculated_hash'][1],
            response._headers['presqt_given_hash'][1])
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/octet-stream')
        # Verify the content length
        self.assertEqual(response._headers['content-length'][1], '1072421328')
        # Verify the fixity was true
        self.assertEqual(response._headers['presqt_fixity'][1], 'True')
        # Run the file downloaded from the fixity checker to check if the
        # file we got from teh response is the same that we sent.
        fixity = fixity_checker(response.content, hashes)
        self.assertEqual(fixity['fixity'], True)

    def test_200_success_hash_with_none_google_drive_osf(self):
        """
        Return a 200 if the GET method is successful when downloading OSF resources from a storage
        provider that doesn't provide hashes
        """
        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': '5cd98a30f2c01100177156be'})
        response = self.client.get(url, **self.header)
        binary_file = response.content
        h = hashlib.md5(binary_file)
        hash_hex = h.hexdigest()

        # Verify the Status Code
        self.assertEqual(response.status_code, 200)
        # Verify the name
        self.assertEqual(
            response._headers['content-disposition'][1],
            'attachment; filename=Character Sheet - Alternative - Print Version.pdf')
        # Verify the hash algorithm that is provided in the header
        # exists in the expected hashes.
        self.assertEqual(response._headers['presqt_hash_algorithm'][1], 'md5')
        self.assertEqual(response._headers['presqt_calculated_hash'][1], hash_hex)
        self.assertEqual(response._headers['presqt_given_hash'][1], 'None')
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/octet-stream')
        # Verify the fixity was true
        self.assertEqual(response._headers['presqt_fixity'][1], 'True')

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
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response._headers['presqt_fixity'][1], 'False')
            self.assertNotEqual(hashes[response._headers['presqt_hash_algorithm'][1]],
                             response._headers['presqt_calculated_hash'][1])
            self.assertNotEqual(response._headers['presqt_calculated_hash'][1],
                             response._headers['presqt_given_hash'][1])

    def test_get_error_400_folder_id(self):
        """
        Return a 400 if a resource ID provided is not that of a file.
        """
        url = reverse('resource_download', kwargs={'target_name': 'osf',
                                                   'resource_id': '5cd9832cf244ec0021e5f245'})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "Resource with id, '5cd9832cf244ec0021e5f245', "
                                                  "is not a file."})

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


    def test_get_error_404_bad_target_name_osf(self):
        """
        Return a 404 if the GET method fails because a bad target_name was given.
        """
        url = reverse('resource_download', kwargs={'target_name': 'bad_name', 'resource_id': '3'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {'error': "'bad_name' is not a valid Target name."})

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
