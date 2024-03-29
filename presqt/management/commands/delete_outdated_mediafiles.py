import os

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
        if os.environ['ENVIRONMENT'] == 'development':
            print('***delete_outdated_mediafiles is running in development mode.***')

        directories_list = [
            '/usr/src/app/mediafiles/jobs/*/',
            '/usr/src/app/mediafiles/bag_tool/*/'
        ]
        directories = []
        [directories.extend(glob(directory)) for directory in directories_list]

        for directory in directories:
            try:
                data = read_file('{}process_info.json'.format(directory), True)
            except (FileNotFoundError, KeyError):
                shutil.rmtree(directory)
                print('{} has been deleted. No process_info.json file found'.format(directory))
            else:
                for key, value in data.items():
                    if 'expiration' in value.keys():
                        if parse(value['expiration']) <= timezone.now() or os.environ['ENVIRONMENT'] == 'development':
                            shutil.rmtree(directory)
                            print('{} has been deleted.'.format(directory))
                            break
                else:
                    if os.environ['ENVIRONMENT'] == 'development':
                        shutil.rmtree(directory)
                        print('{} has been deleted.'.format(directory))
                    else:
                        print('{} has been retained.'.format(directory))
