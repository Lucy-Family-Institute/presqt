
from dateutil.parser import parse
import glob
import json
import shutil

from django.core.management import BaseCommand
from django.utils import timezone

from presqt.api_v1.utilities.io.read_file import read_file


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """
        Delete all mediafiles that have run past their
        expiration date.
        """
        for directory in glob.glob('mediafiles/downloads/*/'):
            for metadata in glob.glob(directory + 'process_info.json'):
                data = read_file(metadata, True)

                expiration = parse(data['expiration'])

                if expiration <= timezone.now():
                    shutil.rmtree(directory)
                    print(directory + ' has been deleted.')

                else:
                    print(directory + ' has been retained.')
