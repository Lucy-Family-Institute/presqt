import json
import shutil
from unittest.mock import patch

import requests
from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import FIGSHARE_TEST_USER_TOKEN
from presqt.targets.figshare.utilities.delete_users_projects_figshare import \
    delete_users_projects_figshare
from presqt.targets.figshare.utilities.helpers.create_article import create_article
from presqt.targets.figshare.utilities.helpers.create_project import create_project
from presqt.targets.utilities import process_wait
from presqt.utilities import read_file, PresQTError


class TestResourceGETJSON(SimpleTestCase):
    """
    Test the `api_v1/targets/figshare/resources/{resource_id}.json/` endpoint's GET method.

    Testing FigShare integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': FIGSHARE_TEST_USER_TOKEN}
        self.keys = ['kind', 'kind_name', 'id', 'title', 'date_created', 'date_modified', 'hashes',
                     'extra', 'links', 'actions']

    def test_success_project(self):
        """
        Returns a 200 if the GET method is successful when getting a FigShare `project`.
        """
        resource_id = '83375'
        extra_keys = ["funding", "collaborators", "description", "custom_fields"]

        url = reverse('resource', kwargs={'target_name': 'figshare',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        for key in extra_keys:
            self.assertIn(key, list(response.data['extra'].keys()))
        # Spot check some individual fields
        self.assertEqual('project', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('Hello World', response.data['title'])
        # Detail Link
        self.assertEqual(len(response.data['links']), 4)

    def test_success_public_project(self):
        """
        Returns a 200 if the GET method is successful when getting a FigShare `project`.
        """
        resource_id = '82529'
        extra_keys = ["funding", "collaborators", "description", "custom_fields"]

        url = reverse('resource', kwargs={'target_name': 'figshare',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        for key in extra_keys:
            self.assertIn(key, list(response.data['extra'].keys()))
        # Spot check some individual fields
        self.assertEqual('project', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual(
            'Post Pregnancy Family Planning Choices in the Public and Private Sectors in Kenya and Indonesia', response.data['title'])
        # Detail Link
        self.assertEqual(len(response.data['links']), 4)

    def test_success_article(self):
        """
        Returns a 200 if the GET method is successful when getting a FigShare `article`.
        """
        resource_id = '83375:12533801'
        extra_keys = ["funding", "version", "resource_doi", "citation"]

        url = reverse('resource', kwargs={'target_name': 'figshare',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        for key in extra_keys:
            self.assertIn(key, list(response.data['extra'].keys()))
        # Spot check some individual fields
        self.assertEqual('figure', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('Ecoute', response.data['title'])
        # Detail Link
        self.assertEqual(len(response.data['links']), 4)

    def test_success_public_article(self):
        """
        Returns a 200 if the GET method is successful when getting a FigShare `article`.
        """
        resource_id = '82529:12541559'
        extra_keys = ["funding", "version", "resource_doi", "citation"]

        url = reverse('resource', kwargs={'target_name': 'figshare',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        for key in extra_keys:
            self.assertIn(key, list(response.data['extra'].keys()))
        # Spot check some individual fields
        self.assertEqual('online resource', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('PPFP Choices Kenya and Indonesia Facility Assessment Tools',
                         response.data['title'])
        # Detail Link
        self.assertEqual(len(response.data['links']), 4)

    def test_success_file(self):
        """
        Returns a 200 if the GET method is successful when getting a FigShare `file`.
        """
        resource_id = '83375:12533801:23301149'
        extra_keys = ["size"]

        url = reverse('resource', kwargs={'target_name': 'figshare',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        for key in extra_keys:
            self.assertIn(key, list(response.data['extra'].keys()))
        # Spot check some individual fields
        self.assertEqual('file', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual('ecoute.png', response.data['title'])
        # Detail Link
        self.assertEqual(len(response.data['links']), 2)

    def test_success_public_file(self):
        """
        Returns a 200 if the GET method is successful when getting a FigShare `file`.
        """
        resource_id = '82529:12541559:23316914'
        extra_keys = ["size"]

        url = reverse('resource', kwargs={'target_name': 'figshare',
                                          'resource_id': resource_id,
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        for key in extra_keys:
            self.assertIn(key, list(response.data['extra'].keys()))
        # Spot check some individual fields
        self.assertEqual('file', response.data['kind_name'])
        self.assertEqual(resource_id, response.data['id'])
        self.assertEqual(
            'PPFP Choices_Charurat_IRB7462_Facility Assessment Tool_V6_28 Feb.doc', response.data['title'])
        # Detail Link
        self.assertEqual(len(response.data['links']), 2)

    def test_error_401_not_authorized_token(self):
        """
        Return a 401 if the GET method fails because the token is invalid.
        """
        url = reverse('resource', kwargs={'target_name': 'figshare',
                                          'resource_id': '1r66j101q13',
                                          'resource_format': 'json'})
        response = self.client.get(url, **{'HTTP_PRESQT_SOURCE_TOKEN': 'EggmundBoi'})
        # Verify the error status code and message
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.data, {'error': "Token is invalid. Response returned a 401 status code."})

    def test_error_404_not_found_project(self):
        """
        Return a 404 if the GET method fails because the user doesn't have access to this resource
        or it doesn't exist.
        """
        url = reverse('resource', kwargs={'target_name': 'figshare',
                                          'resource_id': '18749720',
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data, {'error': "The resource could not be found by the requesting user."})

    def test_error_404_not_found_article(self):
        """
        Return a 404 if the GET method fails because the user doesn't have access to this resource
        or it doesn't exist.
        """
        url = reverse('resource', kwargs={'target_name': 'figshare',
                                          'resource_id': '18749720:12903908',
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data, {'error': "The resource could not be found by the requesting user."})

    def test_error_404_not_found_file(self):
        """
        Return a 404 if the GET method fails because the user doesn't have access to this resource
        or it doesn't exist.
        """
        url = reverse('resource', kwargs={'target_name': 'figshare',
                                          'resource_id': '18749720:12903908:noway',
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data, {'error': "The resource could not be found by the requesting user."})

    def test_error_found_article_but_not_file(self):
        """
        Return a 404 if the GET method fails because the user doesn't have access to this resource
        or it doesn't exist.
        """
        url = reverse('resource', kwargs={'target_name': 'figshare',
                                          'resource_id': '2529:12541559:00000000',
                                          'resource_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data, {'error': "The resource could not be found by the requesting user."})


class TestResourcePost(SimpleTestCase):
    """
    Test the endpoint's POST method for resource uploads:
         `api_v1/targets/{target_name}/resources/{resource_id}/`
         `api_v1/targets/{target_name}/resources/`

    Testing Figshare integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.token = FIGSHARE_TEST_USER_TOKEN
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': self.token,
                        'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        self.good_zip_file = 'presqt/api_v1/tests/resources/upload/GoodBagIt.zip'
        self.resource_id = None
        self.duplicate_action = 'ignore'
        self.file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'

    def tearDown(self):
        """
        This should run at the end of this test class
        """
        delete_users_projects_figshare(self.token)

    def test_success_202_upload(self):
        """
        This test is more of an integration test rather than a unit test.

        Return a 200 when uploading a new top level container.

        """
        ##### UPLOAD A NEW PROJECT #####
        self.url = reverse('resource_collection', kwargs={'target_name': 'figshare'})

        response = self.client.post(
            self.url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Verify status code and message
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['message'], 'The server is processing the request.')

        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the spawned off process finishes in the background to do further validation
        process_wait(process_info, ticket_path)

        # Verify process_info.json file data
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'finished')
        self.assertEqual(process_info['message'], 'Upload successful.')
        self.assertEqual(process_info['status_code'], '200')
        self.assertEqual(process_info['failed_fixity'], [])
        self.assertEqual(process_info['resources_ignored'], [])
        self.assertEqual(process_info['resources_updated'], [])
        self.assertEqual(process_info['hash_algorithm'], 'md5')

        # delete upload folder
        shutil.rmtree(ticket_path)

        ##### UPLOAD TO EXISTING PROJECT #####
        # Get Project ID
        figshare_headers = {'Authorization': 'token {}'.format(self.token)}
        response_data = requests.get(
            "https://api.figshare.com/v2/account/projects", headers=figshare_headers).json()
        for project_data in response_data:
            if project_data['title'] == 'NewProject':
                project_id = project_data['id']
                project_url = project_data['url']
                break

        # Upload resources to the existing project
        self.duplicate_action = 'ignore'
        url = reverse('resource', kwargs={'target_name': 'figshare', 'resource_id': project_id})
        existing_response = self.client.post(
            url, {'presqt-file': open(self.file, 'rb')}, **self.headers)
        ticket_number = existing_response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Verify status code and message
        self.assertEqual(existing_response.status_code, 202)
        self.assertEqual(existing_response.data['message'], 'The server is processing the request.')

        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the spawned off process finishes in the background to do further validation
        process_wait(process_info, ticket_path)

        # Verify process_info.json file data
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'finished')
        self.assertEqual(process_info['message'], 'Upload successful.')
        self.assertEqual(process_info['status_code'], '200')
        self.assertEqual(process_info['failed_fixity'], [])
        self.assertEqual(process_info['resources_ignored'], [])
        self.assertEqual(process_info['resources_updated'], [])
        self.assertEqual(process_info['hash_algorithm'], 'md5')

        # delete upload folder
        shutil.rmtree(ticket_path)

        ##### UPLOAD TO EXISTING ARTICLE #####
        project_response = requests.get(project_url + '/articles', headers=figshare_headers)
        article_id = project_response.json()[0]['id']
        article_url = reverse('resource', kwargs={
                              'target_name': 'figshare', 'resource_id': '{}:{}'.format(project_id, article_id)})

        existing_article_response = self.client.post(
            article_url, {'presqt-file': open(self.file, 'rb')}, **self.headers)
        ticket_number = existing_article_response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Verify status code and message
        self.assertEqual(existing_article_response.status_code, 202)
        self.assertEqual(
            existing_article_response.data['message'], 'The server is processing the request.')

        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the spawned off process finishes in the background to do further validation
        process_wait(process_info, ticket_path)

        # Verify process_info.json file data
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'finished')
        self.assertEqual(process_info['message'], 'Upload successful.')
        self.assertEqual(process_info['status_code'], '200')
        self.assertEqual(process_info['failed_fixity'], [])
        self.assertEqual(process_info['resources_ignored'], [])
        self.assertEqual(process_info['resources_updated'], [])
        self.assertEqual(process_info['hash_algorithm'], 'md5')

        # delete upload folder
        shutil.rmtree(ticket_path)

    def test_401_unauthorized_user(self):
        """
        If a user does not have a valid FigShare API token, we should return a 401 unauthorized status.
        """
        headers = {'HTTP_PRESQT_DESTINATION_TOKEN': 'eggyboi',
                   'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        self.url = reverse('resource_collection', kwargs={'target_name': 'figshare'})
        response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')}, **headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_job_response = self.client.get(response.data['upload_job'], **headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 401)
        self.assertEqual(upload_job_response.data['message'],
                         "Token is invalid. Response returned a 401 status code.")

        # Delete upload folder
        shutil.rmtree(ticket_path)

    def test_cant_upload_to_file(self):
        """
        Return a 400 if user attempts to upload to a file.
        """
        url = reverse('resource', kwargs={'target_name': 'figshare',
                                          'resource_id': "83375:12533801:23301149"})
        response = self.client.post(url, {'presqt-file': open(self.file, 'rb')}, **self.headers)
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 400)
        self.assertEqual(upload_job_response.data['message'],
                         "Can not upload into an existing file.")

        # Delete upload folder
        shutil.rmtree(ticket_path)

    def test_bad_project_id(self):
        """
        Return a 400 if user attempts to upload to a bad project id.
        """
        url = reverse('resource', kwargs={'target_name': 'figshare',
                                          'resource_id': "itsbad"})
        response = self.client.post(url, {'presqt-file': open(self.file, 'rb')}, **self.headers)
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 400)
        self.assertEqual(
            upload_job_response.data['message'], "Project with id, itsbad, could not be found by the requesting user.")

        # Delete upload folder
        shutil.rmtree(ticket_path)

    def test_bad_article_id(self):
        """
        Return a 400 if user attempts to upload to a bad article id.
        """
        url = reverse('resource', kwargs={'target_name': 'figshare',
                                          'resource_id': "83375:itsbad"})
        response = self.client.post(url, {'presqt-file': open(self.file, 'rb')}, **self.headers)
        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Wait until the spawned off process finishes in the background
        # to do validation on the resulting files
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        upload_job_response = self.client.get(response.data['upload_job'], **self.headers)
        # Ensure the response is what we expect
        self.assertEqual(upload_job_response.data['status_code'], 400)
        self.assertEqual(
            upload_job_response.data['message'], "Article with id, itsbad, could not be found by the requesting user.")

        # Delete upload folder
        shutil.rmtree(ticket_path)

    def test_bad_metadata_request(self):
        """
        Ensure that an error is returned if Figshare doesn't return a 201 status code.
        """
        from presqt.targets.figshare.functions.upload_metadata import figshare_upload_metadata

        self.assertRaises(PresQTError, figshare_upload_metadata,
                          'badToken', 'eggtest', {"bad": "metadata"})

    def test_error_updating_metadata_file(self):
        """
        Test that an error is raised if there's an issue updating a metadata file.
        """
        from presqt.targets.figshare.functions.upload_metadata import figshare_upload_metadata

        # Mock a server error for when a put request is made.
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)

        ##### UPLOAD A NEW PROJECT #####
        self.url = reverse('resource_collection', kwargs={'target_name': 'figshare'})

        response = self.client.post(
            self.url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Verify status code and message
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['message'], 'The server is processing the request.')

        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the spawned off process finishes in the background to do further validation
        process_wait(process_info, ticket_path)

        # Verify process_info.json file data
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'finished')
        self.assertEqual(process_info['message'], 'Upload successful.')
        self.assertEqual(process_info['status_code'], '200')
        self.assertEqual(process_info['failed_fixity'], [])
        self.assertEqual(process_info['resources_ignored'], [])
        self.assertEqual(process_info['resources_updated'], [])
        self.assertEqual(process_info['hash_algorithm'], 'md5')

        # Get Project ID
        figshare_headers = {'Authorization': 'token {}'.format(self.token)}
        response_data = requests.get(
            "https://api.figshare.com/v2/account/projects", headers=figshare_headers).json()
        for project_data in response_data:
            if project_data['title'] == 'NewProject':
                project_id = project_data['id']
                break

        # Now I'll make an explicit call to our metadata function with a mocked server error and ensure
        # it is raising an exception.
        with patch('requests.put') as mock_request:
            mock_request.return_value = mock_req
            # Attempt to update the metadata, but the server is down!
            self.assertRaises(PresQTError, figshare_upload_metadata, self.token, project_id,
                              {"context": {}, "allKeywords": [], "actions": []})

        with patch('requests.post') as mock_request:
            # Attempt to update the metadata, but the server is down!
            self.assertRaises(PresQTError, figshare_upload_metadata, self.token, project_id,
                              {"context": {}, "allKeywords": [], "actions": []})

        # Delete corresponding folder
        shutil.rmtree(ticket_path)

    def test_invalid_metadata_upload(self):
        """
        Ensure that if an invalid metadata file is found, it is renamed and a new valid one is uploaded.
        """
        from presqt.targets.figshare.utilities.helpers.upload_helpers import figshare_file_upload_process

        ##### UPLOAD A NEW PROJECT #####
        self.url = reverse('resource_collection', kwargs={'target_name': 'figshare'})

        response = self.client.post(
            self.url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Verify status code and message
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['message'], 'The server is processing the request.')

        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the spawned off process finishes in the background to do further validation
        process_wait(process_info, ticket_path)

        # Verify process_info.json file data
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'finished')
        self.assertEqual(process_info['message'], 'Upload successful.')
        self.assertEqual(process_info['status_code'], '200')
        self.assertEqual(process_info['failed_fixity'], [])
        self.assertEqual(process_info['resources_ignored'], [])
        self.assertEqual(process_info['resources_updated'], [])
        self.assertEqual(process_info['hash_algorithm'], 'md5')

        # delete upload folder
        shutil.rmtree(ticket_path)

        # Get Project ID
        figshare_headers = {'Authorization': 'token {}'.format(self.token)}
        response_data = requests.get(
            "https://api.figshare.com/v2/account/projects", headers=figshare_headers).json()
        for project_data in response_data:
            if project_data['title'] == 'NewProject':
                project_id = project_data['id']
                break
        # We want to delete the good metadata and replace it with invalid before attempting a reupload
        article_list = requests.get(
            "https://api.figshare.com/v2/account/projects/{}/articles".format(project_id),
            headers=figshare_headers).json()
        for article in article_list:
            if article['title'] == "PRESQT_FTS_METADATA":
                # Check for metadata file
                project_files = requests.get(
                    "{}/files".format(article['url']), headers=figshare_headers).json()
                for file in project_files:
                    if file['name'] == "PRESQT_FTS_METADATA.json":
                        requests.delete("https://api.figshare.com/v2/account/articles/{}/files/{}".format(
                            article['id'], file['id']),
                            headers=figshare_headers)
                        figshare_file_upload_process({"invalid": "no good"}, figshare_headers,
                                                     "PRESQT_FTS_METADATA.json", article['id'])
        # Upload resources to the existing project
        self.duplicate_action = 'ignore'
        url = reverse('resource', kwargs={'target_name': 'figshare', 'resource_id': project_id})
        existing_response = self.client.post(
            url, {'presqt-file': open(self.file, 'rb')}, **self.headers)
        ticket_number = existing_response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Verify status code and message
        self.assertEqual(existing_response.status_code, 202)
        self.assertEqual(existing_response.data['message'], 'The server is processing the request.')

        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the spawned off process finishes in the background to do further validation
        process_wait(process_info, ticket_path)

        # Verify process_info.json file data
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'finished')
        self.assertEqual(process_info['message'], 'Upload successful.')
        self.assertEqual(process_info['status_code'], '200')
        self.assertEqual(process_info['failed_fixity'], [])
        self.assertEqual(process_info['resources_ignored'], [])
        self.assertEqual(process_info['resources_updated'], [])
        self.assertEqual(process_info['hash_algorithm'], 'md5')

        # delete upload folder
        shutil.rmtree(ticket_path)

    def test_duplicate_title(self):
        """
        Ensure if a user uploads a project with a title that already exists on Figshare that we add a counter.
        """
        ##### UPLOAD A NEW PROJECT #####
        self.url = reverse('resource_collection', kwargs={'target_name': 'figshare'})

        response = self.client.post(
            self.url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Verify status code and message
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['message'], 'The server is processing the request.')

        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the spawned off process finishes in the background to do further validation
        process_wait(process_info, ticket_path)

        # Verify process_info.json file data
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'finished')
        self.assertEqual(process_info['message'], 'Upload successful.')
        self.assertEqual(process_info['status_code'], '200')
        self.assertEqual(process_info['failed_fixity'], [])
        self.assertEqual(process_info['resources_ignored'], [])
        self.assertEqual(process_info['resources_updated'], [])
        self.assertEqual(process_info['hash_algorithm'], 'md5')

        # delete upload folder
        shutil.rmtree(ticket_path)

        self.url = reverse('resource_collection', kwargs={'target_name': 'figshare'})

        response = self.client.post(
            self.url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

        ticket_number = response.data['ticket_number']
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Verify status code and message
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['message'], 'The server is processing the request.')

        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Wait until the spawned off process finishes in the background to do further validation
        process_wait(process_info, ticket_path)

        # Verify process_info.json file data
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['status'], 'finished')
        self.assertEqual(process_info['message'], 'Upload successful.')
        self.assertEqual(process_info['status_code'], '200')
        self.assertEqual(process_info['failed_fixity'], [])
        self.assertEqual(process_info['resources_ignored'], [])
        self.assertEqual(process_info['resources_updated'], [])
        self.assertEqual(process_info['hash_algorithm'], 'md5')

        # delete upload folder
        shutil.rmtree(ticket_path)

        # Check that the project exists
        url = reverse('resource_collection', kwargs={'target_name': 'figshare'})
        response = self.client.get(url, **{'HTTP_PRESQT_SOURCE_TOKEN': FIGSHARE_TEST_USER_TOKEN})
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Make a list of titles
        project_titles = [project['title']
                          for project in response.data if project['kind_name'] == 'project']

        self.assertIn('NewProject(PresQT1)', project_titles)

    def test_bad_create_project_request(self):
        """
        Ensure that an error is returned if Figshare doesn't return a 201 status code.
        """
        self.assertRaises(PresQTError, create_project, "Title", {"bad": "nope"}, self.token)
    
    def test_bad_create_article_request(self):
        """
        Ensure that an error is returned if Figshare doesn't return a 201 status code.
        """
        self.assertRaises(PresQTError, create_article, "Title", {"bad": "nope"}, "Lalala")
