import bagit
import zipfile

from django.core.management import BaseCommand

from presqt.utilities import zip_directory


class Command(BaseCommand):
    """
    This command will be used to bag a given directory.
    """
    def handle(self, *args, **kwargs):
        directory = input("Insert path to directory: ")
        name_of_zip = directory.rpartition('/')[2]
        bagit.make_bag(directory)

        zip_directory(directory, './mediafiles/{}.zip'.format(name_of_zip), 'mediafiles/uploads')
