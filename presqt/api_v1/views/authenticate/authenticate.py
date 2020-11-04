import requests

from rest_framework import renderers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import UserAuthentication
from config.settings.base import ORCID_CLIENT_ID, ORCID_CLIENT_SECRET


class Authenticate(APIView):
    renderer_classes = [renderers.JSONRenderer]

    def get(self, request, method):
        try:
            code = request.query_params['code']
        except KeyError:
            return Response(data={
                "error": "'code' not found in query parameters."
            }, status=status.HTTP_400_BAD_REQUEST)

        list_of_methods = ['orcid']

        if method not in list_of_methods:
            return Response(data={
                "error": "'{}' is not a valid method. Please choose one of the following: {}".format(method, list_of_methods)
            }, status=status.HTTP_400_BAD_REQUEST)

        data = {
            "client_id": ORCID_CLIENT_ID,
            "client_secret": ORCID_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "https://developers.google.com/oauthplayground"
        }
        response = requests.post('https://orcid.org/oauth/token',
                                 headers={"Accept": "application/json"},
                                 data=data)
        if response.status_code != 200:
            return Response(data={
                "error": "There was an error authenticating the user."
            }, status=status.HTTP_400_BAD_REQUEST)

        else:
            # Get or create the user based on the ORCID ID
            UserAuthentication.objects.update_or_create(
                auth_id=response.json()['orcid'],
                defaults={"auth_token": response.json()['access_token'],
                          "refresh_token": response.json()['refresh_token']})

            return Response(data={
                "auth_token": response.json()['access_token'],
                "refresh_token": response.json()['refresh_token']
            }, status=status.HTTP_200_OK)
