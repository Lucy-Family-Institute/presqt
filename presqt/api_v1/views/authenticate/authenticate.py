import json

import requests
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.views import APIView


class Authenticate(APIView):
    renderer_classes = [renderers.JSONRenderer]

    def get(self, request, method):
        # TODO: Validate method and auth_code
        auth_code = request.query_params['auth_code']

        data = {
            "client_id": "APP-3L910G6J1YJGTK6H",
            "client_secret": "d9059949-4e33-46bb-8d55-3522eff3bf6f",
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": "https://developers.google.com/oauthplayground"
        }

        headers = {"Accept": "application/json"}

        response = requests.post('https://orcid.org/oauth/token',
                                data=json.dumps(data),
                                headers=headers)

        print(response)
        return Response(data=response.json())