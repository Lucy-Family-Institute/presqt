from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.helpers.function_router import FunctionRouter
from presqt.api_v1.helpers.target_validation import target_validation
from presqt.api_v1.serializers.resource import ResourcesSerializer


class ResourceCollection(APIView):
    """
    **Supported HTTP Methods**

    * GET: Retrieve a summary of all resources for the given Target that a user has access to.
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
                "kind": "container",
                "kind_name": "folder",
                "id": "a02d7b96-a4a9-4521-9913-e3cc68f4d9dc",
                "container": "None"
            },
            {
                "kind": "item",
                "kind_name": "file",
                "id": "5b305f1b-0da6-4a1a-9861-3bb159d94c96",
                "container": "a02d7b96-a4a9-4521-9913-e3cc68f4d9dc"
            }
        ]

        Raises
        ---------
        400: Bad Request

        {
            "error": "'presqt-source-token' missing in the request header."
        }

        404: Not Found
        {
            "error": "'bad_target' is not a valid Target name."
        }

        400: Bad Request
        {
            "error": "'new_target' does not support the action 'resource_collection'."
        }
        """
        action = 'resource_collection'

        try:
            token = request.META['HTTP_PRESQT_SOURCE_TOKEN']
        except KeyError:
            return Response(
                data={'error': "'presqt-source-token' missing in the request header."},
                status=status.HTTP_400_BAD_REQUEST)

        validation = target_validation(target_name, action)
        if validation is not True:
            return validation

        func = getattr(FunctionRouter, '{}_{}'.format(target_name, action))
        resources = func(token)
        serializer = ResourcesSerializer(instance=resources, many=True)

        return Response(serializer.data)