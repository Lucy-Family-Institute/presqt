import os
import uuid

from rest_framework.response import Response

from presqt.api_v1.serializers.resource import ResourcesSerializer
from presqt.api_v1.utilities import (
    target_validation, FunctionRouter, get_source_token, query_validator, hash_tokens, page_links)
from presqt.api_v1.views.resource.base_resource import BaseResource
from presqt.utilities import PresQTValidationError, PresQTResponseException, write_file


class ResourceCollection(BaseResource):
    """
    **Supported HTTP Methods**

    * GET:
        - Retrieve a summary of all resources for the given Target that a user has access to.
    * POST
        -  Upload a top level resource for a user.
    """

    def get(self, request, target_name):
        """
        Retrieve all Resources.

        Parameters
        ----------
        target_name : str
            The string name of the Target resource to retrieve.

        Returns
        -------
        200 : OK
        A list-like JSON representation of all resources for the given Target and token.
        [
            {
                "kind": "container",
                "kind_name": "folder",
                "id": "5cd9832cf244ec0021e5f245",
                "container": "cmn5z:osfstorage",
                "title": "Images",
                "links": [
                    {
                        "name": "Detail",
                        "link": "https://localhost/api_v1/targets/osf/resources/5cd9832cf244ec0021e5f245/",
                        "method": "GET"
                    }
                ]
            },
            {
                "kind": "item",
                "kind_name": "file",
                "id": "5cd98510f244ec001fe5632f",
                "container": "5cd9832cf244ec0021e5f245",
                "title": "22776439564_7edbed7e10_o.jpg",
                "links": [
                    {
                        "name": "Detail",
                        "link": "https://localhost/api_v1/targets/osf/resources/5cd98510f244ec001fe5632f/",
                        "method": "GET"
                    }
                ]
            }
        ]

        400: Bad Request
        {
            "error": "PresQT Error: 'new_target' does not support the action 'resource_collection'."
        }
        or
        {
            "error": "PresQT Error: 'presqt-source-token' missing in the request headers."
        }
        or
        {
            "error": "PresQT Error: The search query is not formatted correctly."
        }

        401: Unauthorized
        {
            "error": "Token is invalid. Response returned a 401 status code.""
        }

        404: Not Found
        {
            "error": "PresQT Error: 'bad_target' is not a valid Target name."
        }
        """
        action = 'resource_collection'

        # Perform token, target, and action validation
        try:
            token = get_source_token(request)
            target_validation(target_name, action)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        query_params = request.query_params
        # Validate the search query if there is one.
        if query_params != {}:
            try:
                query_params_value = query_validator(query_params, target_name)
                if query_params_value.isspace() or query_params_value == '':
                    # If title is empty, we want to only return user resources.
                    query_params = {}
            except PresQTResponseException as e:
                # Catch any errors that happen within the search validation
                return Response(data={'error': e.data}, status=e.status_code)

        # Create a ticket_number directory for progress check-ins
        ticket_number = uuid.uuid4()
        ticket_path = os.path.join('mediafiles', 'collection', str(ticket_number))

        # Create directory and process_info json file
        process_info_obj = {
            'presqt-source-token': hash_tokens(token),
            'total_files': 0,
            'files_finished': 0
        }

        process_info_path = os.path.join(str(ticket_path), 'process_info.json')
        write_file(process_info_path, process_info_obj, True)

        # Fetch the proper function to call
        func = FunctionRouter.get_function(target_name, action)

        # Fetch the target's resources
        try:
            resources, pages = func(token, query_params, process_info_path)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch
            return Response(data={'error': e.data}, status=e.status_code)

        serializer = ResourcesSerializer(instance=resources, many=True, context={
                                         'target_name': target_name,
                                         'request': request})
        linked_pages = page_links(self, target_name, pages)

        return Response({"resources": serializer.data, "pages": linked_pages})
