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
        good_file = 'presqt/api_v1/tests/resources/upload/ProjectBagItToUpload.zip'
        response = self.client.post(self.url, {'presqt-file': open(good_file, 'rb')}, **self.headers)

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
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
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
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
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
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
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
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.call_upload_resources()

        url = reverse('upload_job', kwargs={'ticket_number': self.ticket_number})
        headers = {'HTTP_PRESQT_DESTINATION_TOKEN': '1234'}
        response = self.client.get(url, **headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['error'],
                         "Header 'presqt-destination-token' does not match the 'presqt-destination-token' for this server process.")

        # Delete the newly created project in OSF
        self.delete_osf_project('NewProject')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/uploads/{}'.format(self.ticket_number))

    def test_get_error_404_osf(self):
        """
        Return a 404 if the ticket_number provided is not a valid ticket number.
        """
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.call_upload_resources()

        url = reverse('upload_job', kwargs={'ticket_number': 'bad_ticket'})
        response = self.client.get(url, **self.headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], "Invalid ticket number, 'bad_ticket'.")

        # Delete the newly created project in OSF
        self.delete_osf_project('NewProject')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/uploads/{}'.format(self.ticket_number))

    # def test_get_error_500_401_token_invalid_osf(self):
    #     """
    #     Return a 500 if the BaseResource._upload_resource method running on the server gets a 401 error because the token is invalid.
    #     """
    #     self.headers['HTTP_PRESQT_DESTINATION_TOKEN'] = 'bad_token'
    #     self.call_upload_resources()
    #
    #     url = reverse('upload_job', kwargs={'ticket_number': self.ticket_number})
    #     response = self.client.get(url, **self.headers)
    #
    #     self.assertEqual(response.status_code, 500)
    #     self.assertEqual(response.data,
    #                  {'message': "Token is invalid. Response returned a 401 status code.",
    #                   'status_code': 401})
    #
    #     # Delete corresponding folder
    #     shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_get_error_500_401_not_container_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource method running on the server gets a 401 error because the resource_id provided is not a container
        """
        self.url = reverse('resource_collection', kwargs={'target_name': 'osf'})
        self.call_upload_resources()

        headers = {'Authorization': 'Bearer {}'.format(TEST_USER_TOKEN)}
        for node in requests.get('http://api.osf.io/v2/users/me/nodes', headers=headers).json()['data']:
            if node['attributes']['title'] == 'NewProject':
                storage_data = requests.get(node['relationships']['files']['links']['related']['href'], headers=headers).json()
                folder_data = requests.get(storage_data['data'][0]['relationships']['files']['links']['related']['href'], headers=headers).json()
                file_data = requests.get(folder_data['data'][0]['relationships']['files']['links']['related']['href'], headers=headers).json()
                break

        ticket_number = self.ticket_number
        # Attempt to make a new request to the file resource
        file_id = file_data['data'][0]['id']
        self.url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': file_id})
        self.call_upload_resources()

        url = reverse('upload_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "The Resource provided, {}, is not a container".format(file_id),'status_code': 401})

        # Delete the newly created project in OSF
        self.delete_osf_project('NewProject')

        # Delete corresponding folders
        shutil.rmtree('mediafiles/uploads/{}'.format(self.ticket_number))
        shutil.rmtree('mediafiles/uploads/{}'.format(ticket_number))

    def test_get_error_500_403_unauthorized_resource_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource function running on the server gets a 403 error because the resource is not available with the given token.
        """
        self.url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'q5xmw'})
        self.call_upload_resources()

        url = reverse('upload_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.headers)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "User does not have access to this resource with the token provided.",
                          'status_code': 403})

        # Delete corresponding folders
        shutil.rmtree('mediafiles/uploads/{}'.format(self.ticket_number))

    def test_get_error_500_404_resource_not_found_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource function running on the server gets a 404 error because the resource requested does not exist.
        """
        self.url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'bad_id'})
        self.call_upload_resources()

        url = reverse('upload_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.headers)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                        {'message': "Resource with id 'bad_id' not found for this user.",
                         'status_code': 404})

        # Delete corresponding folders
        shutil.rmtree('mediafiles/uploads/{}'.format(self.ticket_number))


    def test_get_error_500_410_gone_osf(self):
        """
        Return a 500 if the BaseResource._upload_resource function running on the server gets a 410 error because the resource requested no longer exists.
        """
        self.url = reverse('resource', kwargs={'target_name': 'osf', 'resource_id': 'k453b'})

        self.call_upload_resources()

        url = reverse('upload_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.headers)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "The requested resource is no longer available.",
                          'status_code': 410})

        # Delete corresponding folders
        shutil.rmtree('mediafiles/uploads/{}'.format(self.ticket_number))
