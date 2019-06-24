import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.serializers.target import TargetsSerializer, TargetSerializer


class TargetCollection(APIView):
    """
    **Supported HTTP Methods**

    * Get: Retrieve summary representations of all Targets.
    """
    required_scopes = ['read']

    def get(self, request):
        """
        Retrieve all Targets.

        Returns
        -------
        200 : OK
        A list-like JSON representation of all Targets.
        [
            {
                "name": "osf",
                "supported_actions": {
                    "resource_collection": true,
                    "resource_detail": true,
                    "resource_download": true,
                    "resource_upload": true
                },
                "detail": "http://localhost/api_v1/target/osf/"
            },
            {
                "name": "curate_nd",
                "supported_actions": {
                    "resource_collection": true,
                    "resource_detail": true,
                    "resource_download": false
                },
                "detail": "http://localhost/api_v1/target/curate_nd/"
            },
            ...
        ]
        """
        with open('presqt/targets.json') as json_file:
            serializer = TargetsSerializer(instance=json.load(json_file),
                                           many=True,
                                           context={'request': request})

        return Response(serializer.data)

class Target(APIView):
    """
    **Supported HTTP Methods**

    * Get: Retrieve summary representations of a specific Targets.
    """
    required_scopes = ['read']

    def get(self, request, target_name):
        """
        Retrieve details about a specific Target.

        Path Parameters
        ---------------
        target_name : str
            The string name of the Target resource to retrieve.

        Returns
        -------
        200 : OK
        A dictionary like JSON representation of the requested Target resource.
        {
            "name": "osf",
            "supported_actions": {
                "resource_collection": true,
                "resource_detail": true,
                "resource_download": true,
                "resource_upload": true
            }
        }

        404: Not Found
        {
            "error": "Invalid Target Name 'bad_target'"
        }

        """
        with open('presqt/targets.json') as json_file:
            json_data = json.load(json_file)

        # Find the JSON dictionary for the target_name provided
        for data in json_data:
            if data['name'] == target_name:
                serializer = TargetSerializer(instance=data)
                return Response(serializer.data)
        # If the target_name provided is not found in the Target JSON
        else:
            return Response(
                data={'error': "Invalid Target Name '{}'".format(target_name)},
                status=status.HTTP_404_NOT_FOUND)
