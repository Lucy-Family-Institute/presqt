import json
import shutil

import requests
from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import TEST_USER_TOKEN
from presqt.api_v1.utilities import read_file, write_file


class TestUploadJob(TestCase):
    """
    Test the `api_v1/downloads/<ticket_id>/` endpoint's GET method.
    """

    def setUp(self):
        self.client = APIClient()
        self.headers = {'HTTP_PRESQT_DESTINATION_TOKEN': TEST_USER_TOKEN, 'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}

    def call_upload_resources(self):
        """
        Make a POST request to `resource` to begin uploading a resource
        """
        url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        good_file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        response = self.client.post(url, {'presqt-file': open(good_file, 'rb')}, **self.headers)

        # Verify the status code
        self.assertEqual(response.status_code, 202)
        self.ticket_number = response.data['ticket_number']
        self.process_info_path = 'mediafiles/uploads/{}/process_info.json'.format(self.ticket_number)
        process_info = read_file(self.process_info_path, True)

        # Save initial process data that we can use to rewrite to the process_info file for testing
        self.initial_process_info = process_info

        # Wait until the spawned off process finishes in the background
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(self.process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass
        self.assertNotEqual(process_info['status'], 'in_progress')

    @staticmethod
    def delete_osf_project(project_name):
        """
        Find an OSF project by name and delete it.
        """
        headers = {'Authorization': 'Bearer {}'.format(TEST_USER_TOKEN)}
        for node in requests.get('http://api.osf.io/v2/users/me/nodes', headers=headers).json()['data']:
            if node['attributes']['title'] == project_name:
                requests.delete('http://api.osf.io/v2/nodes/{}'.format(node['id']), headers=headers)
                break

    def test_get_success_osf(self):
        """
        Return a 200 if the GET was successful and the resources were uploaded.
        """
        self.call_upload_resources()

        url = reverse('upload_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.headers)

        # Verify the status code and data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Upload successful')
        self.assertEqual(response.data['failed_fixity'], [])
        self.assertEqual(response.data['duplicate_files_ignored'], [])
        self.assertEqual(response.data['duplicate_files_updated'], [])

        # Delete the newly created project in OSF
        self.delete_osf_project('NewProject')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/uploads/{}'.format(self.ticket_number))

    def test_get_success_202_osf(self):
        """
        Return a 202 if the GET was successful and the resource upload is in progress.
        """
        self.call_upload_resources()

        # Update the fixity_info.json to say the resource hasn't finished processing
        write_file(self.process_info_path, self.initial_process_info, True)

        url = reverse('upload_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data, {'message': 'Upload is being processed on the server',
                                         'status_code': None})

        # Delete the newly created project in OSF
        self.delete_osf_project('NewProject')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/uploads/{}'.format(self.ticket_number))

    def test_get_error_400_osf(self):
        """
        Return a 400 if the `presqt-destination-token` is missing in the headers.
        """
        self.call_upload_resources()

        url = reverse('upload_job', kwargs={'ticket_number': self.ticket_number})
        headers = {'HTTP_PRESQT_FILE_DUPLICATE_ACTION': 'ignore'}
        response = self.client.get(url, **headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'],
                         "'presqt-destination-token' missing in the request headers.")

        # Delete the newly created project in OSF
        self.delete_osf_project('NewProject')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/uploads/{}'.format(self.ticket_number))

    def test_get_error_401_osf(self):
        """
        Return a 401 if the 'presqt-destination-token' provided in the header does not match
        the 'presqt-destination-token' in the process_info file.
        """
        self.call_upload_resources()


    # 401 "error": "Header 'presqt-source-token' does not match the presqt-source-token' for this server process."
    # 404 "Invalid ticket number, '1234'."

    # 500 401 "Token is invalid. Response returned a 401 status code."
    # 500 401 "The Resource provided, {}, is not a container"
    # 500 403 "User does not have access to this resource with the token provided."
    # 500 404 "error": "Resource with id 'bad_id' not found for this user."
    # 500 410 "error": "The requested resource is no longer available."