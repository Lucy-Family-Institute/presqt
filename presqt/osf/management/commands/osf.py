import json

from django.core.management import BaseCommand

from config.settings.development import OSF_TOKEN
from presqt.osf.functions.functions import fetch_resources, fetch_resource


class Command(BaseCommand):
    def handle(self, *args, **options):
        print(fetch_resources(OSF_TOKEN))
        print(fetch_resource(OSF_TOKEN, 'https://api.osf.io/v2/nodes/gq92a/', 'project'))
        print(fetch_resource(OSF_TOKEN, 'https://api.osf.io/v2/files/5c5dfe2d22b04e001c2c289b/', 'file'))
        print(fetch_resource(OSF_TOKEN, 'https://api.osf.io/v2/files/5c61a50ce16f5500188f088a/', 'folder'))
