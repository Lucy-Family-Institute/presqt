import io
import json
import shutil
import zipfile

from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from config.settings.base import OSF_TEST_USER_TOKEN
from presqt.utilities import write_file, read_file
from presqt.targets.utilities import call_get_resource_zip
from presqt.api_v1.utilities.fixity.download_fixity_checker import download_fixity_checker


class TestDownloadJob(TestCase):
    """
    Test the `api_v1/downloads/<ticket_id>/` endpoint's GET method.

    Testing OSF Integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN}
        self.resource_id = '5cd98510f244ec001fe5632f'
        self.target_name = 'osf'

    def test_success_200(self):
        """
        Return a 200 along with a zip file of the resource requested.
        """
        call_get_resource_zip(self)

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
        self.assertEqual(len(zip_file.namelist()), 12)

        # Verify the custom hash_file information is correct
        with zip_file.open('osf_download_{}/data/fixity_info.json'.format(self.resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)[0]
            self.assertEqual(zip_json['fixity'], True)
            self.assertEqual(zip_json['fixity_details'],
                             'Source Hash and PresQT Calculated hash matched.')
            self.assertEqual(zip_json['hash_algorithm'], 'sha256')
            self.assertEqual(zip_json['presqt_hash'], self.hashes['sha256'])

        # Run the file through the fixity checker again to make sure it downloaded correctly
        with zip_file.open('osf_download_{}/data/22776439564_7edbed7e10_o.jpg'.format(self.resource_id)) as myfile:
            temp_file = myfile.read()
            fixity, fixity_match = download_fixity_checker(temp_file, self.hashes)
            self.assertEqual(fixity['fixity'], True)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))

    def test_success_202(self):
        """
        Return a 202 if the resource has not finished being prepared on the server.
        """
        call_get_resource_zip(self)

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
