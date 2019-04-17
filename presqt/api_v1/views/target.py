import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class TargetsList(APIView):
    """

    """
    required_scopes = ['read']

    def get(self, request):
        with open('presqt/targets.json') as json_file:
            json_data = json.load(json_file)

        return Response(json_data)

class TargetDetails(APIView):
    """

    """
    required_scopes = ['read']

    def get(self, request, target_name):
        with open('presqt/targets.json') as json_file:
            json_data = json.load(json_file)

        for data in json_data:
            if data['name'] == target_name:
                target_data = data
                return Response(target_data)
        else:
            return Response(
                data={'error': "Invalid Target Name '{}'".format(target_name)},
                status=status.HTTP_400_BAD_REQUEST)
