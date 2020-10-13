import json

from rest_framework import status, renderers
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.serializers.service import ServicesSerializer, ServiceSerializer
from presqt.utilities import read_file


class ServiceCollection(APIView):
    """
    **Supported HTTP Methods**

    * Get: Retrieve summary representations of all Services.
    """

    required_scopes = ['read']
    renderer_classes = [renderers.JSONRenderer]

    def get(self, request):
        """
        Retrieve all Services.

        Returns
        -------
        200 : OK
        A list-like JSON representation of all Services.
        [
            {
                "name": "eaasi",
                "readable_name": "EaaSI",
                "links": [
                    {
                        "name": "Detail",
                        "link": "https://localhost/api_v1/services/eaasi/",
                        "method": "GET"
                    }
                ]
            }
        ]
        """
        with open('presqt/specs/services.json') as json_file:
            serializer = ServicesSerializer(instance=json.load(json_file),
                                           many=True,
                                           context={'request': request})

        return Response(serializer.data)


class Service(APIView):
    """
    **Supported HTTP Methods**

    * Get: Retrieve summary representations of a specific Service.
    """

    required_scopes = ['read']
    renderer_classes = [renderers.JSONRenderer]

    def get(self, request, service_name):
        """
        Retrieve details about a specific Service.

        Path Parameters
        ---------------
        service_name : str
            The string name of the Service to retrieve.

        Returns
        -------
        200 : OK
        A dictionary like JSON representation of the requested Service.
        {
            "name": "eaasi",
            "readable_name": "EaaSI",
            "links": [
                {
                    "name": "Proposals",
                    "link": "https://localhost/api_v1/services/eaasi/proposals/",
                    "method": "POST"
                }
            ]
        }

        404: Not Found
        {
            "error": "PresQT Error: Invalid Service Name 'bad_service'"
        }

        """
        json_data = read_file('presqt/specs/services.json', True)

        # Find the JSON dictionary for the service_name provided
        for data in json_data:
            if data['name'] == service_name:
                serializer = ServiceSerializer(instance=data, context={'request': request})
                return Response(serializer.data)
        # If the service_name provided is not found in the Service JSON
        else:
            return Response(
                data={'error': "PresQT Error: Invalid Service Name '{}'".format(service_name)},
                status=status.HTTP_404_NOT_FOUND)