import json

import requests
from django.core.management import BaseCommand

from config.settings.development import OSF_TOKEN


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('node_id')

    def handle(self, *args, **options):
        '''
        
        DATA OBJECT GOAL
        
        {
            'project_id': 'id',
            'project_title': 'title',
            'project_description': 'description', 
            'storage_providers': [
                {
                    'name = 'osf_storage',
                    'files': [
                        {
                            'file_name': 'name',
                            'download_link': 'link',
                        },
                        {
                            'file_name': 'name2',
                            'download_link': 'link2',
                        }
                    ],
                    'folders': [
                        {
                            'name': 'folder_name',
                            'files': [
                                {
                                'file_name': 'folder_file_name',
                                'download_link': 'folder_file_link',
                                },
                                ...
                            ],
                            'folders': []
                        },
                        ...
                    ]
                },
                ...
            ]
        }
        '''

        node_id = options['node_id']
        headers = {'Authorization': 'Bearer {}'.format(OSF_TOKEN)}

        # Get Project Details + Set up object
        # 'https://api.osf.io/v2/nodes/{node_id}/
        url = 'https://api.osf.io/v2/nodes/{}/'.format(node_id)
        r = requests.get(url, headers=headers)
        r_data = r.json()['data']
        data_obj = {
            'project_id': r_data['id'],
            'project_title': r_data['attributes']['title'],
            'project_description': r_data['attributes']['description'],
            'storage_providers': []
        }

        # Loop through storage providers
        # https://api.osf.io/v2/nodes/{node_id}/files/
        url = r_data['relationships']['files']['links']['related']['href']
        r = requests.get(url, headers=headers)
        for provider in r.json()['data']:
            provider_obj = {
                'name': provider['attributes']['name'],
                'files': [],
                'folders': []
            }
            # Loop through the provider's files
            # https://api.osf.io/v2/nodes/{node_id}/files/{provider}/
            file_url = provider['relationships']['files']['links']['related']['href']
            file_r = requests.get(file_url, headers=headers)
            provider_obj = build_obj(
                file_r.json()['data'], provider_obj, headers, file_r.json()['links']
            )
            data_obj['storage_providers'].append(provider_obj)

        print(json.dumps(data_obj))

def build_obj(file_datas, obj, headers, file_links):
    for file_data in file_datas:
        if file_data['attributes']['kind'] == 'file':
            file_obj = {
                'file_name': file_data['attributes']['name'],
                'download_link': file_data['links']['download']
            }
            obj['files'].append(file_obj)
        elif file_data['attributes']['kind'] == 'folder':
            # https://api.osf.io/v2/nodes/{node_id}/files/{provider}/{path}/
            folder_url = file_data['relationships']['files']['links']['related']['href']
            folder_r = requests.get(folder_url, headers=headers)
            folder_datas = folder_r.json()['data']
            new_obj = {
                    'name': file_data['attributes']['name'],
                    'files': [],
                    'folders': []
            }
            build_obj(folder_datas, new_obj, headers, folder_r.json()['links'])
            obj['folders'].append(new_obj)
    if file_links['next']:
            # https://api.osf.io/v2/nodes/{node_id}/files/{provider}/?page={page_number}
            next_url = file_links['next']
            next_r = requests.get(next_url, headers=headers)
            build_obj(next_r.json()['data'], obj, headers, next_r.json()['links'])
    return obj
