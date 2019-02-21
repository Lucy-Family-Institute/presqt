import os

from django.core.management import BaseCommand
from osfclient import OSF, cli

from config.settings.development import OSF_TOKEN, OSF_PASSWORD


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Get private project with Token
        # project = OSF().project('gq92a')

        # Get a private project with log in credentials
        osf_instance = OSF(username='foxkilgannon@gmail.com', password=OSF_PASSWORD)
        project = osf_instance.project('gq92a')

        # List all files for a given project
        for store in project.storages:
            prefix = store.name
            for file_ in store.files:
                path = file_.path
                if path.startswith('/'):
                    path = path[1:]
                print(os.path.join(prefix, path))