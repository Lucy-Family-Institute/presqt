import io
import json
import shutil
import zipfile
from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from presqt.api_v1.utilities import hash_tokens
from presqt.utilities import read_file
from presqt.targets.utilities import shared_call_get_resource_zip

from config.settings.base import GITHUB_TEST_USER_TOKEN


class TestDownload(SimpleTestCase):
    """
    Test the 'api_v1/downloads/<ticket_id>/' endpoint's GET method.

    Testing only GitHub download function.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': GITHUB_TEST_USER_TOKEN,
                       'HTTP_PRESQT_EMAIL_OPT_IN': ''}
        self.target_name = 'github'
        self.token = GITHUB_TEST_USER_TOKEN

    def test_success_download_private_repo(self):
        """
        Return a 200 along with a zip file of the private repo requested.
        """
        resource_id = '209372336'
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
        with zip_file.open('github_download_{}/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 1)

        file_path = "{}_download_{}/data/PrivateProject/README.md".format(
            self.target_name, resource_id)
        # Verify that the folder exists
        self.assertIn(file_path, zip_file.namelist())

        # Verify there is only one entry that contains this folder
        count_of_file_references = zip_file.namelist().count(file_path)
        self.assertEqual(count_of_file_references, 1)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_success_download_public_repo(self):
        """
        Return a 200 along with a zip file of the public repo requested.
        """
        resource_id = '209373787'
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
        with zip_file.open('github_download_{}/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 1)

        with zip_file.open('github_download_{}/PRESQT_FTS_METADATA.json'.format(resource_id)) as metadatafile:
            metadata = json.load(metadatafile)
            self.assertEqual(metadata['extra_metadata']['description'],
                             "Well, there's not much to describe.")
            self.assertEqual(metadata['extra_metadata']['title'], 'ProjectEight')

        file_path = "{}_download_{}/data/ProjectEight/README.md".format(
            self.target_name, resource_id)
        # Verify that the file exists
        self.assertIn(file_path, zip_file.namelist())

        # Verify there is only one entry that contains this file
        count_of_file_references = zip_file.namelist().count(file_path)
        self.assertEqual(count_of_file_references, 1)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_success_download_unowned_public_repo(self):
        """
        Return a 200 along with a zip file of the unowned public repo requested.
        """
        resource_id = '248'
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
        # self.assertEqual(len(zip_file.namelist()), 13)

        # Verify the fixity file is empty as there was nothing to check.
        with zip_file.open('github_download_{}/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 20)

        file_path = "{}_download_{}/data/rorem/lib/rorem/distribution.rb".format(self.target_name,
                                                                                 resource_id)
        # Verify that the file exists
        self.assertIn(file_path, zip_file.namelist())

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_success_full_code_repo(self):
        """
        Return a 200 along with a zip file of the repo and assosciated files requested.
        """
        resource_id = '209373160'
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
        self.assertEqual(len(zip_file.namelist()), 84)

        # GitHub does not provide file hashes, and thus we can't properly check fixity.
        with zip_file.open('{}_download_{}/fixity_info.json'.format(self.target_name, resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            for file_fixity in zip_json:
                self.assertEqual(file_fixity['fixity_details'],
                                 "Either a Source Hash was not provided or the source hash algorithm is not supported.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_success_directory(self):
        """
        Return a 200 along with a zip file of the directory requested.
        """
        resource_id = '209373160:music%2F__pycache__'
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
        self.assertEqual(len(zip_file.namelist()), 27)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_success_file(self):
        """
        Return a 200 along with a zip file of the file requested.
        """
        resource_id = '209373160:album_uploader%2F__pycache__%2F__init__%2Ecpython-36%2Epyc'
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

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    # def test_success_big_file(self):
    #     """
    #     Return a 200 along with a zip file of the big file requested.
    #     """
    #     resource_id = '266134247:Media_Files%2F20180726_174402%252Emp4'
    #     shared_call_get_resource_zip(self, resource_id)

    #     url = reverse('download_job', kwargs={'ticket_number': self.ticket_number,
    #                                           'response_format': 'zip'})
    #     response = self.client.get(url, **self.header)
    #     # Verify the status code
    #     self.assertEqual(response.status_code, 200)

    #     zip_file = zipfile.ZipFile(io.BytesIO(response.content))

    #     # Verify the name of the zip file
    #     self.assertEquals(
    #         response._headers['content-disposition'][1],
    #         'attachment; filename={}_download_{}.zip'.format(self.target_name, resource_id))
    #     # Verify content type
    #     self.assertEqual(response._headers['content-type'][1], 'application/zip')
    #     # Verify the number of resources in the zip is correct
    #     self.assertEqual(len(zip_file.namelist()), 13)

    #     # Delete corresponding folder
    #     shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_success_file_bad_project(self):
        """
        Return a 200 along with a zip file of the file requested.
        """
        resource_id = '9328472398472398472398423798432984723984723984:album_uploader%2F__pycache__%2F__init__%2Ecpython-36%2Epyc'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('job_status', kwargs={'action': 'download',
                                            'response_format': 'zip'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 500)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_success_file_bad_file_path(self):
        """
        Return a 200 along with a zip file of the file requested.
        """
        resource_id = '209373160:bad%2Ffile%2Fpath%2E.py'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('job_status', kwargs={'action': 'download',
                                            'response_format': 'zip'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 500)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_error_500_401(self):
        """
        Return a 500 if an invalid token is provided.
        """
        url = reverse('resource', kwargs={'target_name': self.target_name,
                                          'resource_id': '209373160',
                                          'resource_format': 'zip'})

        response = self.client.get(url, **{'HTTP_PRESQT_SOURCE_TOKEN': 'eggs',
                                           'HTTP_PRESQT_EMAIL_OPT_IN': ''})
        ticket_number = hash_tokens('eggs')
        download_url = response.data['download_job_zip']
        process_info_path = 'mediafiles/jobs/{}/process_info.json'.format(ticket_number)
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
        shutil.rmtree('mediafiles/jobs/{}'.format(ticket_number))

    def test_error_500_404(self):
        """
        Return a 500 if an invalid resource_id is provided.
        """
        url = reverse('resource', kwargs={'target_name': self.target_name,
                                          'resource_id': 'bad',
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
                         "The resource with id, bad, does not exist for this user.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(ticket_number))
