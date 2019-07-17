import os

import bagit
import requests
from django.core.management import BaseCommand

from config.settings.base import TEST_USER_TOKEN


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        bagit.make_bag('presqt/FolderUpdateBagItToUpload')
        # header = {'Authorization': 'Bearer {}'.format(TEST_USER_TOKEN)}
        # nodes = requests.get('http://api.osf.io/v2/users/me/nodes', headers=header)
        # for node in nodes.json()['data']:
        #     if node['attributes']['title'] == 'Test Project':
        #         print(requests.get(node['relationships']['files']['links']['related']['href']).json())
        #         break
