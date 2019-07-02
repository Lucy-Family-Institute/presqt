import os

from django.core.management import BaseCommand

from config.settings.base import TEST_USER_TOKEN
from presqt.api_v1.utilities import read_file
from presqt.osf.classes.main import OSF
from presqt.osf.helpers import get_osf_resource


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        osf_instance = OSF(TEST_USER_TOKEN)
        resource = get_osf_resource('5dxev:osfstorage', osf_instance)

        # To create a new folder
        # new_folder = resource.create_folder('new_folder', True)

        # To create a new project
        # new_project = osf_instance.create_project('New Project')

        # To create a new file
        # file = read_file('mediafiles/uploads/ba467255-516f-46ce-8efa-543238559547/osf_download_cmn5z:osfstorage/data/osfstorage/Docs/build-plugins.js')
        # resource.create_file('build-plugins.js', file)

        # To write a directory
        resource.create_directory('mediafiles/uploads/d38cce21-cd73-4ee3-ba24-46ccda0f0dfb/osf_download_5cd98b0af244ec0021e5f8dd/data')