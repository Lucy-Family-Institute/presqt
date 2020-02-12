import io
import json
import shutil
import zipfile

from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import OSF_TEST_USER_TOKEN
from presqt.api_v1.utilities.fixity.download_fixity_checker import download_fixity_checker
from presqt.utilities import write_file, read_file
from presqt.targets.utilities import shared_call_get_resource_zip


class TestDownloadJobGET(SimpleTestCase):
    """
    Test the `api_v1/downloads/<ticket_id>/` endpoint's GET method.

    Testing only PresQT core code.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN}
        self.resource_id = '5cd98510f244ec001fe5632f'
        self.target_name = 'osf'
        self.hashes = {
            "sha256": "3e517cda95ddbfcb270ab273201517f5ae0ee1190a9c5f6f7e6662f97868366f",
            "md5": "9e79fdd9032629743fca52634ecdfd86"}

    def test_success_200(self):
        """
        Return a 200 along with a zip file of the resource requested.
        """
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
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
        with zip_file.open('osf_download_{}/data/fixity_info.json'.format(self.resource_id)) as fixityfile:
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
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_success_202(self):
        """
        Return a 202 if the resource has not finished being prepared on the server.
        """
        shared_call_get_resource_zip(self, self.resource_id)

        # Update the fixity_info.json to say the resource hasn't finished processing
        write_file(self.process_info_path, self.initial_process_info, True)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        # Verify the status code and content
        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.data, {'message': 'Download is being processed on the server', 'status_code': None})

        # Verify the status of the process_info file is 'in_progress'
        process_info = read_file(self.process_info_path, True)
        self.assertEqual(process_info['status'], 'in_progress')

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_400(self):
        """
        Return a 400 if the 'presqt-source-token' is missing in the headers
        """
        shared_call_get_resource_zip(self, self.resource_id)

        header = {}
        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **header)

        # Verify the status code and content
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'],
                         "'presqt-source-token' missing in the request headers.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_401(self):
        """
        Return a 401 if the 'presqt-source-token' provided in the header does not match
        the 'presqt-source-token' in the process_info file.
        """
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        headers = {'HTTP_PRESQT_SOURCE_TOKEN': '1234'}
        response = self.client.get(url, **headers)

        # Verify the status code and content
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['error'],
                         "Header 'presqt-source-token' does not match the 'presqt-source-token' "
                         "for this server process.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_404(self):
        """
        Return a 404 if the ticket_number provided is not a valid ticket number.
        """
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('download_job', kwargs={'ticket_number': 'bad_ticket'})
        response = self.client.get(url, **self.header)

        # Verify the status code and content
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], "Invalid ticket number, 'bad_ticket'.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_500_401_token_invalid(self):
        """
        Return a 500 if the Resource._download_resource() method running on the server gets a 401 error
        """
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': '1234'}
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "Token is invalid. Response returned a 401 status code.",
                          'status_code': 401})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_500_403_unauthorized_container_resource(self):
        """
        Return a 500 if the Resource._download_resource() function running on the server gets a 403 error
        """
        self.resource_id = 'q5xmw'
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "User does not have access to this resource with the token provided.",
                          'status_code': 403})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_500_403_unauthorized_item_resource(self):
        """
        Return a 500 if the Resource._download_resource() function running on the server gets a 403 error
        """
        self.resource_id = '5cd98c2cf244ec0020e4d9d1'
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "User does not have access to this resource with the token provided.",
                          'status_code': 403})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_500_404_resource_not_found(self):
        """
        Return a 500 if the Resource._download_resource() function running on the server gets a 404 error
        """
        self.resource_id = 'bad_id'
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "Resource with id 'bad_id' not found for this user.",
                          'status_code': 404})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_500_410_gone(self):
        """
        Return a 500 if the Resource._download_resource() function running on the server gets a 410 error
        """
        self.resource_id = '5cd989c5f8214b00188af9b5'
        shared_call_get_resource_zip(self, self.resource_id)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data,
                         {'message': "The requested resource is no longer available.",
                          'status_code': 410})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

class TestDownloadJobPATCH(SimpleTestCase):
    """
    Test the `api_v1/downloads/<ticket_id>/` endpoint's PATCH method.

    Testing only PresQT core code.
    """
    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN}
        self.resource_id = '5cd98510f244ec001fe5632f'
        self.target_name = 'osf'

        download_url = reverse('resource', kwargs={'target_name': self.target_name,
                                                   'resource_id': self.resource_id,
                                                   'resource_format': 'zip'})
        download_response = self.client.get(download_url, **self.header)


        download_job_patch = reverse('download_job', kwargs={'ticket_number': download_response.data['ticket_number']})
        download_job_patch_response = self.client.patch(download_job_patch, **self.header)
        print(download_job_patch_response.data)
