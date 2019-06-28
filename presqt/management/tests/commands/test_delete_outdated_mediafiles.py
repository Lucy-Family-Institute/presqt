import glob
import json
import multiprocessing
import os

from dateutil.relativedelta import relativedelta

from django.core.management import call_command
from django.conf import settings
from django.test.testcases import TestCase
from django.utils import timezone

from presqt.api_v1.utilities import write_file
from presqt.api_v1.utilities.io.read_file import read_file
from presqt.api_v1.views.resource.resource import download_resource


class TestDeleteMediaFiles(TestCase):
    def setUp(self):
        self.directory = 'mediafiles/downloads/test_command/'
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.data = ({"presqt-source-token": "blahblah", "status": "in_progress",
                      "expiration": str(timezone.now()+relativedelta(days=5)),
                      "message": "Download successful", "status_code": "200",
                      "zip_name": "test.zip"})
        with open('{}process_info.json'.format(self.directory), 'w+') as file:
            json.dump(self.data, file)

        # Download file into test directory
        process_state = multiprocessing.Value('b', 0)
        download_resource('osf', 'resource_download', settings.PRIVATE_USER_TOKEN,
                          '5cd98978f244ec001ee86609', self.directory, '{}process_info.json'.format(
                              self.directory), process_state)

    def test_files_to_be_retained(self):
        """
        This test is to ensure that if the expiration listed in process_info is not before the
        current date, the data that has been downloaded in this folder will be retained.
        """
        data_pre_command = glob.glob('mediafiles/downloads/test_command/process_info.json')
        self.assertEqual(len(data_pre_command), 1)

        call_command('delete_outdated_mediafiles')

        # Ensure that the folder and files have been retained
        data_post_command = glob.glob('mediafiles/downloads/test_command/')
        self.assertEqual(len(data_post_command), 1)

    def test_files_to_delete(self):
        """
        This test is to ensure that if the expiration listed in process_info is before the
        current date, that data that has been downloaded will be deleted.
        """
        # These steps are required to alter the timestamp inside our process_info.json
        data = read_file('{}process_info.json'.format(self.directory), True)

        # Set the expiration date to be yesterday
        data['expiration'] = str(timezone.now() - relativedelta(days=1))

        # Write the data JSON back to the process_info file
        write_file('{}process_info.json'.format(self.directory), data, True)

        data_pre_command = glob.glob('mediafiles/downloads/test_command/process_info.json')
        self.assertEqual(len(data_pre_command), 1)

        call_command('delete_outdated_mediafiles')

        # Check that the folder has been deleted
        data_post_command = glob.glob('mediafiles/downloads/test_command/')
        self.assertEqual(len(data_post_command), 0)
