
from dateutil.parser import parse
import glob
import shutil

from django.core.management import BaseCommand
from django.utils import timezone

from presqt.api_v1.utilities.io.read_file import read_file


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """
        Delete all mediafiles that have run past their expiration date.
        """
        for directory in glob.glob('mediafiles/downloads/*/'):
            data = read_file('{}process_info.json'.format(directory), True)

            expiration = parse(data['expiration'])

            if expiration <= timezone.now():
                shutil.rmtree(directory)
                print('{} has been deleted.'.format(directory))
            else:
                print('{} has been retained.'.format(directory))
