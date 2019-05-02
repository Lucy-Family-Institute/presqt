from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.helpers.function_router import FunctionRouter
from presqt.api_v1.serializers.resource import ResourcesSerializer


class ResourceCollection(APIView):
    """
    **Supported HTTP Methods**

    * Get: Retrieve a summary of all resources for the given Target that a user has access to.
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
                "container": "None",
                "title": "Folder Name"
            },
            {
                "kind": "item",
                "kind_name": "file",
                "id": "5b305f1b-0da6-4a1a-9861-3bb159d94c96",
                "container": "a02d7b96-a4a9-4521-9913-e3cc68f4d9dc",
                "title": "file.jpg"
            }
        ]

        Resources
        ---------
        400: Bad Request

        {
            "error": "'presqt-source-token' missing in the request header."
        }

        401: Runtime Error
        {
            "error": "The Token provided is not authorized to access this asset."
        }

        404: Not Found
        {
            "error": "'bad_target' is not a valid Target name."
        }

        """
        # Retrieve the token from the header
        try:
            token = request.META['HTTP_PRESQT_SOURCE_TOKEN']
        except KeyError:
            return Response(
                data={'error': "'presqt-source-token' missing in the request header."},
                status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the appropriate function for the given Target Name
        try:
            func = getattr(FunctionRouter, '{}_list'.format(target_name))
        except AttributeError:
            return Response(
                data={'error': "'{}' is not a valid Target name.".format(target_name)},
                status=status.HTTP_404_NOT_FOUND)

        # Call the function that retrieves resources for the given Target.
        try:
            resources = func(token)
        except RuntimeError:
            return Response(
                data={'error': "The Token provided is not authorized to access this asset."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                data={'error': e}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ResourcesSerializer(instance=resources, many=True)

        return Response(serializer.data)