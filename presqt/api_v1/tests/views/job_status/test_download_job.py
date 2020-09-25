import io
import json
import shutil
import zipfile

from django.core import mail
from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import OSF_TEST_USER_TOKEN
from presqt.api_v1.utilities import hash_tokens
from presqt.api_v1.utilities.fixity.download_fixity_checker import download_fixity_checker
from presqt.utilities import write_file, read_file
from presqt.targets.utilities import shared_call_get_resource_zip


class TestDownloadJobGET(SimpleTestCase):
    """
    Test the `api_v1/job_status/download/` endpoint's GET method.

    Testing only PresQT core code.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN,
                       'HTTP_PRESQT_EMAIL_OPT_IN': ''}
        self.resource_id = '5cd98510f244ec001fe5632f'
        self.target_name = 'osf'
        self.hashes = {
            "sha256": "3e517cda95ddbfcb270ab273201517f5ae0ee1190a9c5f6f7e6662f97868366f",
            "md5": "9e79fdd9032629743fca52634ecdfd86"}
        self.ticket_number = hash_tokens(OSF_TEST_USER_TOKEN)
        self.token = OSF_TEST_USER_TOKEN

    def test_success_200_zip(self):
        """
        Return a 200 along with a zip file of the resource requested.
        """
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('job_status', kwargs={'action': 'download', 'response_format': 'zip'})
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
        self.assertEqual(len(zip_file.namelist()), 13)

        # Verify the custom hash_file information is correct
        with zip_file.open('osf_download_{}/fixity_info.json'.format(self.resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], True)
            self.assertEqual(zip_json['fixity_details'],
                             'Source Hash and PresQT Calculated hash matched.')
            self.assertIn(zip_json['hash_algorithm'], ['sha256', 'md5'])
            self.assertEqual(zip_json['presqt_hash'], self.hashes[zip_json['hash_algorithm']])

        # Run the file through the fixity checker again to make sure it downloaded correctly
        with zip_file.open('osf_download_{}/data/22776439564_7edbed7e10_o.jpg'.format(self.resource_id)) as myfile:
            temp_file = myfile.read()
            resource_dict = {
                "file": temp_file,
                "hashes": self.hashes,
                "title": '22776439564_7edbed7e10_o.jpg',
                "path": 'osf_download_{}/data/22776439564_7edbed7e10_o.jpg'.format(self.resource_id),
                "metadata": {}
            }
            fixity, fixity_match = download_fixity_checker(resource_dict)
            self.assertEqual(fixity['fixity'], True)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

        # Ensure no email was sent for this request as no email was provided.
        self.assertEqual(len(mail.outbox), 0)

    def test_success_200_json(self):
        """
        Return a 200 along with a zip file of the resource requested.
        """
        self.header['HTTP_PRESQT_EMAIL_OPT_IN'] = 'test@fakeemail.com'
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('job_status', kwargs={'action': 'download', 'response_format': 'json'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)

        # Verify the status code and data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Download successful.')
        self.assertEqual(response.data['failed_fixity'], [])

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_success_202(self):
        """
        Return a 202 if the resource has not finished being prepared on the server.
        """
        shared_call_get_resource_zip(self, self.resource_id)

        # Update the fixity_info.json to say the resource hasn't finished processing
        write_file(self.process_info_path, self.initial_process_info, True)

        url = reverse('job_status', kwargs={'action': 'download'})
        response = self.client.get(url, **self.header)

        # Verify the status code and content
        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.data['message'], 'Download is being processed on the server')

        # Verify the status of the process_info file is 'in_progress'
        process_info = read_file(self.process_info_path, True)
        self.assertEqual(process_info['resource_download']['status'], 'in_progress')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_error_400_bad_action(self):
        """
        Return a 400 if the 'action' query parameter is bad
        """
        shared_call_get_resource_zip(self, self.resource_id)

        header = {}
        url = reverse('job_status', kwargs={'action': 'bad_action'})
        response = self.client.get(url, **header)

        # Verify the status code and content
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'],
                         "PresQT Error: 'bad_action' is not a valid acton.")

    def test_error_400(self):
        """
        Return a 400 if the 'presqt-source-token' is missing in the headers
        """
        shared_call_get_resource_zip(self, self.resource_id)

        header = {}
        url = reverse('job_status', kwargs={'action': 'download'})
        response = self.client.get(url, **header)

        # Verify the status code and content
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'],
                         "PresQT Error: 'presqt-source-token' missing in the request headers.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_success_400_bad_format(self):
        """
        Return a 400 if the given response_format is bad.
        """
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('job_status', kwargs={'action': 'download',
                                            'response_format': 'bad_format'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 400)

        # Verify the status code and data
        self.assertEqual(response.data['error'],
                         'PresQT Error: bad_format is not a valid format for this endpoint.')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_error_404(self):
        """
        Return a 404 if the ticket_number provided is not a valid ticket number.
        """
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'bad_token'}
        url = reverse('job_status', kwargs={'action': 'download'})
        response = self.client.get(url, **header)
        # Verify the status code and content
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], "PresQT Error: Invalid ticket number, '{}'.".format(
            hash_tokens('bad_token')))

    def test_error_500_401_token_invalid(self):
        """
        Return a 500 if the Resource._download_resource() method running on the server gets a 401 error
        """
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': '1234'}
        self.token = '1234'
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('job_status', kwargs={'action': 'download'})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['message'],
                         "Token is invalid. Response returned a 401 status code.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_error_500_403_unauthorized_container_resource(self):
        """
        Return a 500 if the Resource._download_resource() function running on the server gets a 403 error
        """
        self.resource_id = 'q5xmw'
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('job_status', kwargs={'action': 'download'})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['message'],
                         "User does not have access to this resource with the token provided.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_error_500_403_unauthorized_item_resource(self):
        """
        Return a 500 if the Resource._download_resource() function running on the server gets a 403 error
        """
        self.resource_id = '5cd98c2cf244ec0020e4d9d1'
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('job_status', kwargs={'action': 'download'})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['message'],
                         "User does not have access to this resource with the token provided.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_error_500_404_resource_not_found(self):
        """
        Return a 500 if the Resource._download_resource() function running on the server gets a 404 error
        """
        self.resource_id = 'bad_id'
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('job_status', kwargs={'action': 'download'})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['message'],
                         "Resource with id 'bad_id' not found for this user.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_error_500_410_gone(self):
        """
        Return a 500 if the Resource._download_resource() function running on the server gets a 410 error
        """
        self.resource_id = '5cd989c5f8214b00188af9b5'
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('job_status', kwargs={'action': 'download'})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['message'],
                         "The requested resource is no longer available.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))


class TestDownloadJobPATCH(SimpleTestCase):
    """
    Test the `api_v1/job_status/download/` endpoint's PATCH method.

    Testing only PresQT core code.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN,
                       'HTTP_PRESQT_EMAIL_OPT_IN': ''}
        self.resource_id = 'cmn5z'
        self.target_name = 'osf'
        self.ticket_number = hash_tokens(OSF_TEST_USER_TOKEN)
        self.token = OSF_TEST_USER_TOKEN

    def test_success_200(self):
        """
        Return a 200 for successful cancelled download process.
        """
        download_url = reverse('resource', kwargs={'target_name': self.target_name,
                                                   'resource_id': self.resource_id,
                                                   'resource_format': 'zip'})
        self.client.get(download_url, **self.header)

        ticket_path = 'mediafiles/jobs/{}'.format(self.ticket_number)
        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['resource_download']['status'], 'in_progress')

        # Wait until the spawned off process has a function_process_id to cancel the download
        while not process_info['resource_download']['function_process_id']:
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        download_patch_url = reverse('job_status', kwargs={'action': 'download'})
        download_patch_url_response = self.client.patch(download_patch_url, **self.header)

        self.assertEquals(download_patch_url_response.status_code, 200)

        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        download_process_info = process_info['resource_download']

        self.assertEquals(download_process_info['message'], 'Download was cancelled by the user')
        self.assertEquals(download_process_info['status'], 'failed')
        self.assertEquals(download_process_info['status_code'], '499')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_success_406(self):
        """
        Return a 406 for unsuccessful cancel because the download finished already.
        """
        download_url = reverse('resource', kwargs={'target_name': self.target_name,
                                                   'resource_id': '5cd98510f244ec001fe5632f',
                                                   'resource_format': 'zip'})
        self.client.get(download_url, **self.header)

        ticket_path = 'mediafiles/jobs/{}'.format(self.ticket_number)
        # Verify process_info file status is 'in_progress' initially
        process_info = read_file('{}/process_info.json'.format(ticket_path), True)
        self.assertEqual(process_info['resource_download']['status'], 'in_progress')

        # Wait until the spawned off process finishes to attempt to cancel download
        while process_info['resource_download']['status'] == 'in_progress':
            try:
                process_info = read_file('{}/process_info.json'.format(ticket_path), True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        download_patch_url = reverse('job_status', kwargs={'action': 'download'})
        download_patch_url_response = self.client.patch(download_patch_url, **self.header)

        self.assertEquals(download_patch_url_response.status_code, 406)
        self.assertEquals(download_patch_url_response.data['message'], 'Download successful.')

        process_info = read_file('{}/process_info.json'.format(ticket_path), True)

        self.assertEquals(process_info['resource_download']['message'], 'Download successful.')
        self.assertEquals(process_info['resource_download']['status'], 'finished')
        self.assertEquals(process_info['resource_download']['status_code'], '200')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_error_400(self):
        """
        Return a 400 if the 'presqt-source-token' is missing in the headers
        """
        header = {}
        url = reverse('job_status', kwargs={'action': 'download'})
        response = self.client.patch(url, **header)

        # Verify the status code and content
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'],
                         "PresQT Error: 'presqt-source-token' missing in the request headers.")

    def test_success_400_bad_format(self):
        """
        Return a 400 if the given response_format is bad.
        """
        shared_call_get_resource_zip(self, '5cd98510f244ec001fe5632f')

        url = reverse('job_status', kwargs={'action': 'download',
                                            'response_format': 'bad_format'})
        response = self.client.patch(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 400)

        # Verify the status code and data
        self.assertEqual(response.data['error'],
                         'PresQT Error: bad_format is not a valid format for this endpoint.')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))
