from django.core.management import BaseCommand

import requests

from config.settings.development import OSF_TOKEN


class Command(BaseCommand):
    def handle(self, *args, **options):
        headers = {'Authorization': 'Bearer {}'.format(OSF_TOKEN)}

        url = 'https://api.osf.io/v2/users/me/nodes/'
        r = requests.get(url, headers=headers)
        r_data = r.json()['data']

        node_list = []

        for node in r_data:
            data_obj = {
                'id': node['id'],
                'project_link': node['links']['self'],
                'title': node['attributes']['title'],
                'description': node['attributes']['description'],
                'tags': node['attributes']['tags']
            }
            node_list.append(data_obj)
        print(node_list)
