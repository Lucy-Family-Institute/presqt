import base64
import json
import shutil

import requests
from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import FIGSHARE_TEST_USER_TOKEN
from presqt.targets.figshare.utilities.delete_users_projects_figshare import \
    delete_users_projects_figshare
from presqt.targets.github.functions.upload_metadata import github_upload_metadata
from presqt.targets.github.utilities import delete_github_repo
from presqt.targets.utilities import shared_upload_function_github, process_wait
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
        self.assertEqual(len(response.data['links']), 2)

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
        self.assertEqual(len(response.data['links']), 2)

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
        self.assertEqual(len(response.data['links']), 2)

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
        self.assertEqual(len(response.data['links']), 2)

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
        self.url = reverse('resource_collection', kwargs={'target_name': 'figshare'})

        response = self.client.post(self.url, {'presqt-file': open(self.file, 'rb')}, **self.headers)

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
        response_data = requests.get("https://api.figshare.com/v2/account/projects", headers=figshare_headers).json()
        for project_data in response_data:
            if project_data['title'] == 'NewProject':
                project_id = project_data['id']

        # Upload resources to the existing project
        self.duplicate_action = 'ignore'
        url = reverse('resource', kwargs={'target_name': 'figshare', 'resource_id': project_id})
        existing_response = self.client.post(url, {'presqt-file': open(self.file, 'rb')}, **self.headers)
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

        # Re-upload to make sure a duplicate is not made

        # Upload file to existing article
