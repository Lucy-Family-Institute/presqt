
from dateutil.parser import parse
from glob import glob
import shutil

from django.core.management import BaseCommand
from django.utils import timezone

from presqt.utilities import read_file


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """
        Delete all mediafiles that have run past their expiration date.
        """
        directories_list = [
            'mediafiles/downloads/*/',
            'mediafiles/uploads/*/',
            'mediafiles/transfers/*/'
        ]
        directories = []
        [directories.extend(glob(directory)) for directory in directories_list]

        for directory in directories:
            data = read_file('{}process_info.json'.format(directory), True)

            expiration = parse(data['expiration'])

            if expiration <= timezone.now():
                shutil.rmtree(directory)
                print('{} has been deleted.'.format(directory))
            else:
                print('{} has been retained.'.format(directory))
