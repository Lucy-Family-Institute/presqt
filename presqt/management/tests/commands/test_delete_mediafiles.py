import glob
import json
import os
import shutil

from dateutil.relativedelta import relativedelta

from django.core.management import call_command
from django.test.testcases import TestCase
from django.utils import timezone

from presqt.management.commands.delete_mediafiles import Command


class TestDeleteMediaFiles(TestCase):
    def setUp(self):
        self.directory = 'mediafiles/downloads/test_command/'
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.data = ({"presqt-source-token": "blahblah", "status": "finished", "expiration": str(timezone.now()+relativedelta(days=5)),
                      "kill_time": "2019-06-13 15:38:18.229257+00:00", "message": "Download successful",
                      "status_code": "200", "zip_name": "test.zip"})
        with open(self.directory + 'process_info.json', 'w+') as file:
            json.dump(self.data, file)

    def test_files_to_be_retained(self):
        """
        This test is to ensure that if the expiration listed in process_info is not before the
        current date, the data that has been downloaded in this folder will be retained.
        """
        data_pre_command = glob.glob(
            'mediafiles/downloads/test_command/process_info.json')
        self.assertEqual(len(data_pre_command), 1)

        call_command('delete_mediafiles')

        # Ensure that the folder and files have been retained
        data_post_command = glob.glob(
            'mediafiles/downloads/test_command/')
        self.assertEqual(len(data_post_command), 1)

    def test_files_to_delete(self):
        """
        This test is to ensure that if the expiration listed in process_info is before the
        current data, that data that has been downloaded will be deleted.
        """
        # These steps are required to alter the timestamp inside our process_info.json
        in_file = open(self.directory + 'process_info.json', 'r')

        data_file = in_file.read()
        data = json.loads(data_file)

        # Set the expiration date to be yesterday
        data['expiration'] = str(timezone.now() - relativedelta(days=1))
        out_file = open(self.directory + 'process_info.json', 'w')
        out_file.write(json.dumps(data))
        out_file.close()

        data_pre_command = glob.glob(
            'mediafiles/downloads/test_command/process_info.json')
        self.assertEqual(len(data_pre_command), 1)

        call_command('delete_mediafiles')

        # Check that the folder has been deleted
        data_post_command = glob.glob(
            'mediafiles/downloads/test_command/')
        self.assertEqual(len(data_post_command), 0)
