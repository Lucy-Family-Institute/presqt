
from dateutil.parser import parse
import glob
import json
import shutil

from django.core.management import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """
        Delete all mediafiles that have run past their
        expiration date.
        """
        for directory in glob.glob('mediafiles/downloads/*/'):
            for metadata in glob.glob(directory + 'process_info.json'):
                with open(metadata) as server_metadata:
                    data = json.load(server_metadata)
                    # Convert string datetime into a datetime object
                    expiration = parse(data['expiration'])

                    if expiration <= timezone.now():
                        shutil.rmtree(directory)
                        print(directory + ' has been deleted.')

                    else:
                        print(directory + ' has been retained.')
