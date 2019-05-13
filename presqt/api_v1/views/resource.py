from rest_framework.response import Response

from rest_framework import status
from rest_framework.views import APIView

from presqt.api_v1.helpers.function_router import FunctionRouter
from presqt.api_v1.helpers.validation import target_validation, token_validation
from presqt.api_v1.serializers.resource import ResourcesSerializer, ResourceSerializer
from presqt.exceptions import (PresQTValidationError, PresQTAuthorizationError,
                               PresQTResponseException)


class ResourceCollection(APIView):
    """
    **Supported HTTP Methods**

    * GET: Retrieve a summary of all resources for the given Target that a user has access to.
    """
    required_scopes = ['read']

    def get(self, request, target_name):
        """
        Retrieve all Resources.

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

        Raises
        ---------
        400: Bad Request
        {
            "error": "'new_target' does not support the action 'resource_collection'."
        }

        401: Unauthorized
        {
            "error": "'presqt-source-token' missing in the request headers."
        }

        404: Not Found
        {
            "error": "'bad_target' is not a valid Target name."
        }
        """
        action = 'resource_collection'

        # Perform token validation
        try:
            token = token_validation(request)
        except PresQTAuthorizationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Perform target_name and action validation
        try:
            target_validation(target_name, action)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Fetch the proper function to call
        func = getattr(FunctionRouter, '{}_{}'.format(target_name, action))

        # Fetch the target's resources
        try:
            resources = func(token)
        except Exception as e:
            # Catch any errors that happen within the target fetch
            return Response(data={'error': e.__str__()}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ResourcesSerializer(instance=resources, many=True)
        return Response(serializer.data)


class Resource(APIView):
    """
    **Supported HTTP Methods**

    * GET: Retrieve a summary of the resource for the given Target that has been requested.
    """
    required_scopes = ['read']

    def get(self, request, target_name, resource_id):
        """
        Retrieve details about a specific Resource.

        Parameters
        ----------
        target_name : str
            The name of the Target resource to retrieve.
        resource_id : str
            The id of the Resource to retrieve.

        Returns
        -------
        A dictionary like JSON representation of the requested Target resource.
        {
            'id': '5cd9831c054f5b001a5ca2af',
            'title': '2017-01-27 PresQT Workshop Planning Meeting Items.docx'
        }

        Raises
        ------
        400: Bad Request
        {
            "error": "'new_target' does not support the action 'resource_collection'."
        }

        401: Unauthorized
        {
            "error": "'presqt-source-token' missing in the request headers."
        }

        404: Not Found
        {
            "error": "'bad_target' is not a valid Target name."
        }
        """
        action = 'resource_detail'

        # Perform token validation
        try:
            token = token_validation(request)
        except PresQTAuthorizationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Perform target_name and action validation
        try:
            target_validation(target_name, action)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Fetch the proper function to call
        func = getattr(FunctionRouter, '{}_{}'.format(target_name, action))

        # Fetch the resource
        try:
            resource = func(token, resource_id)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch
            return Response(data={'error': e.data}, status=e.status_code)

        serializer = ResourceSerializer(instance=resource)
        return Response(serializer.data)


class ResourceDownload(APIView):
    """
    **Supported HTTP Methods**

    * GET: Download a single file with the given resource ID provided.
    """

    def get(self, request, target_name, resource_id):
        """

        Parameters
        ----------
        request
        target_name
        resource_id

        Returns
        -------

        """
        action = 'resource_download'

        # Perform token validation
        try:
            token = token_validation(request)
        except PresQTAuthorizationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Perform target_name and action validation
        try:
            target_validation(target_name, action)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Fetch the proper function to call
        func = getattr(FunctionRouter, '{}_{}'.format(target_name, action))

        return Response({'We did it': 'yay!'})