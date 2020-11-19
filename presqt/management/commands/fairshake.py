import json
import coreapi

import requests
from django.core.management import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        api_key = 'd9fb202a16298dfc4fa098be452c49e23861d160'
        project_id = 116
        client = coreapi.Client(auth=coreapi.auth.TokenAuthentication(
            token=api_key, scheme='token'))
        schema = client.get('https://fairshake.cloud/coreapi/')

        ### THIS CREATES THE DIGITAL_OBJECT ###
        obj = client.action(schema, ['digital_object', 'create'], params=dict(
            url='https://github.com/ndlib/presqt-ui',
            title='presqt-ui',
            projects=[project_id],
            type='tool'
        ))
        ### DIGITAL_OBJECT ID ###
        obj_id = obj['id']

        # obj at this point =
        # {
        #   "id": <obj_id>,
        #   "projects": [116],
        #   "description": "",
        #   "image": "",
        #   "tags": "",
        #   "type": "tool",
        #   "title": "presqt-ui",
        #   "url": "https://github.com/ndlib/presqt-ui",
        #   "authors": [224],
        #   "rubrics": []
        # }
        # print(obj_id)

        # TODO: ADD CODE TO RUN ASSESSMENTS HERE

        # This should be the call to get scores
        # Replace target with obj_id
        score = client.action(schema, ['score', 'list'], params=dict(
            target=obj_id
        ))
        print(score)
