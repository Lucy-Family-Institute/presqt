import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.serializers.target import TargetsSerializer, TargetSerializer
from presqt.utilities import read_file


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
                "readable_name": "OSF",
                "supported_actions": {
                    "resource_collection": true,
                    "resource_detail": true,
                    "resource_download": true,
                    "resource_upload": true,
                    "resource_transfer_in": true,
                    "resource_transfer_out": true
                },
                "supported_transfer_partners": {
                    "transfer_in": [
                        "github",
                        "curate_nd"
                    ],
                    "transfer_out": [
                        "github"
                    ]
                },
                "supported_hash_algorithms": [
                    "sha256",
                    "md5"
                ],
                "links": [
                    {
                        "name": "Detail",
                        "link": "https://localhost/api_v1/targets/osf/",
                        "method": "GET"
                    }
                ]
            },
            {
                "name": "curate_nd",
                "readable_name": "CurateND",
                "supported_actions": {
                    "resource_collection": true,
                    "resource_detail": true,
                    "resource_download": true,
                    "resource_upload": false,
                    "resource_transfer_in": false,
                    "resource_transfer_out": true
                },
                "supported_transfer_partners": {
                    "transfer_in": [],
                    "transfer_out": [
                        "osf",
                        "github"
                    ]
                },
                "supported_hash_algorithms": [
                    "md5"
                ],
                "links": [
                    {
                        "name": "Detail",
                        "link": "https://localhost/api_v1/targets/curate_nd/",
                        "method": "GET"
                    }
                ]
            },...
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
            "readable_name": "OSF",
            "supported_actions": {
                "resource_collection": true,
                "resource_detail": true,
                "resource_download": true,
                "resource_upload": true,
                "resource_transfer_in": true,
                "resource_transfer_out": true
            },
            "supported_transfer_partners": {
                "transfer_in": [
                    "github",
                    "curate_nd"
                ],
                "transfer_out": [
                    "github"
                ]
            },
            "supported_hash_algorithms": [
                "sha256",
                "md5"
            ],
            "links": [
                {
                    "name": "Collection",
                    "link": "https://localhost/api_v1/targets/osf/resources/",
                    "method": "GET"
                },
                {
                    "name": "Upload",
                    "link": "https://localhost/api_v1/targets/osf/resources/",
                    "method": "POST"
                },
                {
                    "name": "Transfer",
                    "link": "https://localhost/api_v1/targets/osf/resources/",
                    "method": "POST"
                }
            ]
        }

        404: Not Found
        {
            "error": "Invalid Target Name 'bad_target'"
        }

        """
        json_data = read_file('presqt/targets.json', True)

        # Find the JSON dictionary for the target_name provided
        for data in json_data:
            if data['name'] == target_name:
                serializer = TargetSerializer(instance=data, context={'request': request})
                return Response(serializer.data)
        # If the target_name provided is not found in the Target JSON
        else:
            return Response(
                data={'error': "Invalid Target Name '{}'".format(target_name)},
                status=status.HTTP_404_NOT_FOUND)
