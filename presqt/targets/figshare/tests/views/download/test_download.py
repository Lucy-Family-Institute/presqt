import io
import json
import shutil
import zipfile
from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from presqt.utilities import read_file
from presqt.targets.utilities import shared_call_get_resource_zip
from presqt.api_v1.utilities import hash_tokens

from config.settings.base import FIGSHARE_TEST_USER_TOKEN


class TestDownload(SimpleTestCase):
    """
    Test the 'api_v1/downloads/<ticket_id>/' endpoint's GET method.

    Testing only FigShare download function.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': FIGSHARE_TEST_USER_TOKEN}
        self.target_name = 'figshare'
        self.token = FIGSHARE_TEST_USER_TOKEN

    def test_success_download_private_project(self):
        """
        Return a 200 along with a zip file of the private project requested.
        """
        resource_id = '83375'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('job_status', kwargs={'action': 'download',
                                            'response_format': 'zip'})
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
        self.assertEqual(len(zip_file.namelist()), 14)

        # Verify the fixity file is empty as there was nothing to check.
        with zip_file.open('figshare_download_{}/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 1)

        file_path = "{}_download_{}/data/Hello World/Ecoute/ecoute.png".format(
            self.target_name, resource_id)
        # Verify that the folder exists
        self.assertIn(file_path, zip_file.namelist())

        count_of_file_references = zip_file.namelist().count(file_path)
        self.assertEqual(count_of_file_references, 1)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(hash_tokens(self.token)))

    def test_success_download_public_project(self):
        """
        Return a 200 along with a zip file of the public project requested.
        """
        resource_id = '82718'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('job_status', kwargs={'action': 'download',
                                            'response_format': 'zip'})
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
        self.assertEqual(len(zip_file.namelist()), 71)

        # Verify the fixity file is empty as there was nothing to check.
        with zip_file.open('figshare_download_{}/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 57)

        file_path = "{}_download_{}/data/ASFV alignment/Multiple sequence alignment for identification of divergent selection of MGF505/MGF360/MGF505-2R-4R.aln.fasta".format(
            self.target_name, resource_id)
        # Verify that the folder exists
        self.assertIn(file_path, zip_file.namelist())

        count_of_file_references = zip_file.namelist().count(file_path)
        self.assertEqual(count_of_file_references, 1)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(hash_tokens(self.token)))

    def test_success_download_private_article(self):
        """
        Return a 200 along with a zip file of the private article requested.
        """
        resource_id = '83375:12533801'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('job_status', kwargs={'action': 'download',
                                            'response_format': 'zip'})
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

        # Verify the fixity file is empty as there was nothing to check.
        with zip_file.open('figshare_download_{}/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 1)

        file_path = "{}_download_{}/data/Ecoute/ecoute.png".format(
            self.target_name, resource_id)
        # Verify that the folder exists
        self.assertIn(file_path, zip_file.namelist())

        count_of_file_references = zip_file.namelist().count(file_path)
        self.assertEqual(count_of_file_references, 1)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(hash_tokens(self.token)))

    def test_success_download_public_article(self):
        """
        Return a 200 along with a zip file of the private article requested.
        """
        resource_id = '82529:12541559'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('job_status', kwargs={'action': 'download',
                                            'response_format': 'zip'})
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
        self.assertEqual(len(zip_file.namelist()), 14)

        # Verify the fixity file is empty as there was nothing to check.
        with zip_file.open('figshare_download_{}/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 2)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(hash_tokens(self.token)))

    def test_success_download_private_file(self):
        """
        Return a 200 along with a zip file of the private file requested.
        """
        resource_id = '83375:12533801:23301149'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('job_status', kwargs={'action': 'download',
                                            'response_format': 'zip'})
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

        # Verify the fixity file is empty as there was nothing to check.
        with zip_file.open('figshare_download_{}/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 1)

        file_path = "{}_download_{}/data/ecoute.png".format(
            self.target_name, resource_id)
        # Verify that the folder exists
        self.assertIn(file_path, zip_file.namelist())

        count_of_file_references = zip_file.namelist().count(file_path)
        self.assertEqual(count_of_file_references, 1)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(hash_tokens(self.token)))

    def test_success_download_public_file(self):
        """
        Return a 200 along with a zip file of the private article requested.
        """
        resource_id = '82529:12541559:23316914'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('job_status', kwargs={'action': 'download',
                                            'response_format': 'zip'})
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

        # Verify the fixity file is empty as there was nothing to check.
        with zip_file.open('figshare_download_{}/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 1)

        file_path = "{}_download_{}/data/PPFP Choices_Charurat_IRB7462_Facility Assessment Tool_V6_28 Feb.doc".format(
            self.target_name, resource_id)
        # Verify that the folder exists
        self.assertIn(file_path, zip_file.namelist())

        count_of_file_references = zip_file.namelist().count(file_path)
        self.assertEqual(count_of_file_references, 1)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(hash_tokens(self.token)))

    def test_error_500_401(self):
        """
        Return a 500 if an invalid token is provided.
        """
        url = reverse('resource', kwargs={'target_name': self.target_name,
                                          'resource_id': '209373160',
                                          'resource_format': 'zip'})

        response = self.client.get(url, **{'HTTP_PRESQT_SOURCE_TOKEN': 'eggs'})
        download_url = response.data['download_job_zip']
        process_info_path = 'mediafiles/jobs/{}/process_info.json'.format(hash_tokens('eggs'))
        process_info = read_file(process_info_path, True)

        while process_info['resource_download']['status'] == 'in_progress':
            try:
                process_info = read_file(process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        download_response = self.client.get(download_url, **{'HTTP_PRESQT_SOURCE_TOKEN': 'eggs'})
        # The endpoint lumps all errors into a 500 status code
        self.assertEqual(download_response.status_code, 500)
        self.assertEqual(download_response.data['status_code'], 401)
        self.assertEqual(download_response.data['message'],
                         "Token is invalid. Response returned a 401 status code.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(hash_tokens('eggs')))

    def test_error_500_404_bad_project_id(self):
        """
        Return a 500 if an invalid resource_id is provided.
        """
        url = reverse('resource', kwargs={'target_name': self.target_name,
                                          'resource_id': 'bad',
                                          'resource_format': 'zip'})

        response = self.client.get(url, **self.header)
        download_url = response.data['download_job_zip']
        process_info_path = 'mediafiles/jobs/{}/process_info.json'.format(hash_tokens(self.token))
        process_info = read_file(process_info_path, True)

        while process_info['resource_download']['status'] == 'in_progress':
            try:
                process_info = read_file(process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        download_response = self.client.get(download_url, **self.header)
        # The endpoint lumps all errors into a 500 status code
        self.assertEqual(download_response.status_code, 500)
        self.assertEqual(download_response.data['status_code'], 404)
        self.assertEqual(download_response.data['message'],
                         "The resource could not be found by the requesting user.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(hash_tokens(self.token)))

    def test_error_500_404_bad_article_id(self):
        """
        Return a 500 if an invalid resource_id is provided.
        """
        url = reverse('resource', kwargs={'target_name': self.target_name,
                                          'resource_id': '82529:nah',
                                          'resource_format': 'zip'})

        response = self.client.get(url, **self.header)
        ticket_number = hash_tokens(self.token)
        download_url = response.data['download_job_zip']
        process_info_path = 'mediafiles/jobs/{}/process_info.json'.format(ticket_number)
        process_info = read_file(process_info_path, True)

        while process_info['resource_download']['status'] == 'in_progress':
            try:
                process_info = read_file(process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        download_response = self.client.get(download_url, **self.header)
        # The endpoint lumps all errors into a 500 status code
        self.assertEqual(download_response.status_code, 500)
        self.assertEqual(download_response.data['status_code'], 404)
        self.assertEqual(download_response.data['message'],
                         "The resource could not be found by the requesting user.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(ticket_number))

    def test_error_500_404_bad_file_id(self):
        """
        Return a 500 if an invalid resource_id is provided.
        """
        url = reverse('resource', kwargs={'target_name': self.target_name,
                                          'resource_id': '82529:12541559:not_a_file',
                                          'resource_format': 'zip'})

        response = self.client.get(url, **self.header)
        ticket_number = hash_tokens(self.token)
        download_url = response.data['download_job_zip']
        process_info_path = 'mediafiles/jobs/{}/process_info.json'.format(ticket_number)
        process_info = read_file(process_info_path, True)

        while process_info['resource_download']['status'] == 'in_progress':
            try:
                process_info = read_file(process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        download_response = self.client.get(download_url, **self.header)
        # The endpoint lumps all errors into a 500 status code
        self.assertEqual(download_response.status_code, 500)
        self.assertEqual(download_response.data['status_code'], 404)
        self.assertEqual(download_response.data['message'],
                         "The resource could not be found by the requesting user.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(ticket_number))
