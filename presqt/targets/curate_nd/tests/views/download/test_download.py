import io
import json
import shutil
import zipfile
import time

from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import CURATE_ND_TEST_TOKEN
from presqt.api_v1.utilities.fixity.download_fixity_checker import download_fixity_checker
from presqt.utilities import read_file
from presqt.targets.utilities import shared_call_get_resource_zip


class TestDownload(TestCase):
    """
    Test the 'api_v1/downloads/<ticket_id>/' endpoint's GET method.

    Testing only CurateND download function.
    """
    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': CURATE_ND_TEST_TOKEN}
        self.target_name = 'curate_nd'

    def test_success_empty_item(self):
        """
        Return a 200 along with a zip file of the empty item requested.
        """
        resource_id = 'hq37vm4432z'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename={}_download_{}.zip'.format(self.target_name, resource_id))

        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 11)

        # Verify the fixity file is empty as there was nothing to check.
        with zip_file.open('curate_nd_download_{}/data/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 0)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_success_individual_file(self):
        """
        Return a 200 along with a zip file of the file requested.
        """
        resource_id = 'd504rj4616d'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename={}_download_{}.zip'.format(self.target_name, resource_id))
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 12)

        # Verify the custom hash_file information is correct
        with zip_file.open('{}_download_{}/data/fixity_info.json'.format(self.target_name, resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], True)
            self.assertEqual(zip_json['fixity_details'],
                             'Source Hash and PresQT Calculated hash matched.')
            self.assertEqual(zip_json['hash_algorithm'], 'md5')
            self.assertEqual(zip_json['presqt_hash'], zip_json['source_hash'])

        # Run the file through the fixity checker again to make sure it downloaded correctly
        with zip_file.open('{}_download_{}/data/1900s_Cat.jpg'.format(self.target_name, resource_id)) as myfile:
            temp_file = myfile.read()
            fixity, fixity_match = download_fixity_checker(temp_file, {'md5': zip_json['presqt_hash']})
            self.assertEqual(fixity['fixity'], True)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_success_item_multiple_files(self):
        """
        Return a 200 along with a zip file of the item and assosciated files requested.
        """
        resource_id = 'dj52w379504'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename={}_download_{}.zip'.format(self.target_name, resource_id))
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 13)

        # Verify the custom hash_file information is correct
        with zip_file.open('{}_download_{}/data/fixity_info.json'.format(self.target_name, resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            for file_fixity in zip_json:
                self.assertEqual(file_fixity['fixity'], True)
                self.assertEqual(file_fixity['fixity_details'],
                                'Source Hash and PresQT Calculated hash matched.')
                self.assertEqual(file_fixity['hash_algorithm'], 'md5')
                self.assertEqual(file_fixity['presqt_hash'], file_fixity['source_hash'])

        # Run the files through the fixity checker again to make sure they downloaded correctly
        with zip_file.open('{}_download_{}/data{}'.format(
            self.target_name, resource_id, zip_json[0]['path'])) as myfile:
            temp_file = myfile.read()
            fixity, fixity_match = download_fixity_checker(temp_file, {'md5': zip_json[0]['presqt_hash']})
            self.assertEqual(fixity['fixity'], True)
        with zip_file.open('{}_download_{}/data{}'.format(
            self.target_name, resource_id, zip_json[1]['path'])) as myfile:
            temp_file = myfile.read()
            fixity, fixity_match = download_fixity_checker(temp_file, {'md5': zip_json[1]['presqt_hash']})
            self.assertEqual(fixity['fixity'], True)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_error_500_401(self):
        """
        Return a 500 if an invalid token is provided.
        """
        url = reverse('resource', kwargs={'target_name': self.target_name,
                                          'resource_id': 'dj52w379504',
                                          'resource_format': 'zip'})

        response = self.client.get(url, **{'HTTP_PRESQT_SOURCE_TOKEN': 'eggs'})
        ticket_number = response.data['ticket_number']
        download_url = response.data['download_job']
        process_info_path = 'mediafiles/downloads/{}/process_info.json'.format(ticket_number)
        process_info = read_file(process_info_path, True)
        # Adding a brief sleep to allow the download_job endpoint to not return a 202 as it loads
        while process_info['status'] == 'in_progress':
            try:
                process_info = read_file(process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass
        
        download_response = self.client.get(download_url, **{'HTTP_PRESQT_SOURCE_TOKEN': 'eggs'})
        # The endpoint lumps all errors into a 500 status code
        self.assertEqual(download_response.status_code, 500)
        self.assertEqual(download_response.data['status_code'], 401)
        self.assertEqual(download_response.data['message'], "Token is invalid. Response returned a 401 status code.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(ticket_number))

    def test_error_500_403_unauthorized_item_resource(self):
        """
        Return a 500 if the Resource._download_resource() function running on the server gets a 403 error
        """
        self.resource_id = 'ns064458c6g'
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
                         {'message': "Resource not found.",
                          'status_code': 404})

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))
