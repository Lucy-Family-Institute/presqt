import json

import requests
from django.core.management import BaseCommand


class Command(BaseCommand):
  def handle(self, *args, **kwargs):
    fairshake_url = 'https://fairshake.cloud/digital_object/?format=api'
    headers = {'Authorization': 'token d9fb202a16298dfc4fa098be452c49e23861d160',
               'Content-Type': 'application/json',
               'accept': 'application/json'}
    data = {
      "projects": [
        116
      ],
      "title": "presqt-ui",
      "url": "https://github.com/ndlib/presqt-ui"
    }

    response = requests.post(fairshake_url, headers=headers, data=data)
    print(response.status_code)