from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.helpers.function_router import FunctionRouter
from presqt.api_v1.serializers.resource import ResourcesSerializer


class ResourcesList(APIView):
    """
    **Supported HTTP Methods**

    * Get: Retrieve a summary of all resources for the given Target.
    """
    required_scopes = ['read']

    def get(self, request, target_name):
        """

        Parameters
        ----------
        target_name : str
            The string name of the Target resource to retrieve.

        Returns
        -------
        A list-like JSON representation of all resources for the given Target and token.

        [
            {
                "kind": "folder",
                "kind_name": "google_drive",
                "id": "a02d7b96-a4a9-4521-9913-e3cc68f4d9dc",
                "container": "None"
            },
            {
                "kind": "file",
                "kind_name": "name!",
                "id": "5b305f1b-0da6-4a1a-9861-3bb159d94c96",
                "container": "a02d7b96-a4a9-4521-9913-e3cc68f4d9dc"
            }
        ]

        Resources
        ---------
        400: Bad Request

        {
            "error": "'presqt-source-token' missing in the request header."
        }

        400: Bad Request
        {
            "error": "'bad_target' is not a valid Target name."
        }
        """
        try:
            token = request.META['HTTP_PRESQT_SOURCE_TOKEN']
        except KeyError:
            return Response(
                data={'error': "'presqt-source-token' missing in the request header."},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            func = getattr(FunctionRouter, '{}_list'.format(target_name))
        except AttributeError:
            return Response(
                data={'error': "'{}' is not a valid Target name.".format(target_name)},
                status=status.HTTP_400_BAD_REQUEST)

        resources = func(token)
        serializer = ResourcesSerializer(instance=resources, many=True)

        return Response(serializer.data)
