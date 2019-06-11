import json
import os
import shutil
from datetime import timedelta, datetime
import multiprocessing
from uuid import uuid4

import bagit
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


from presqt.api_v1.serializers.resource import ResourcesSerializer, ResourceSerializer
from presqt.api_v1.utilities import (token_validation, target_validation, FunctionRouter,
                                     write_file, zip_directory)
from presqt.api_v1.utilities.io.read_file import read_file
from presqt.exceptions import (PresQTValidationError, PresQTAuthorizationError,
                               PresQTResponseException)
from presqt import fixity


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
        200 : OK
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

        400: Bad Request
        {
            "error": "'new_target' does not support the action 'resource_collection'."
        }
        or
        {
            "error": "'presqt-source-token' missing in the request headers."
        }

        401: Unauthorized
        {
            "error": "Token is invalid. Response returned a 401 status code.""
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
        func = FunctionRouter.get_function(target_name, action)

        # Fetch the target's resources
        try:
            resources = func(token)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch
            return Response(data={'error': e.data}, status=e.status_code)

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
        200: OK
        A dictionary like JSON representation of the requested Target resource.
        {
            "kind": "item",
            "kind_name": "file",
            "id": "5cd98518f244ec001ee8606b",
            "title": "23296359282_934200ec59_o.jpg",
            "date_created": "2019-05-13T14:54:17.129170Z",
            "date_modified": "2019-05-13T14:54:17.129170Z",
            "size": 1773294,
            "hashes": {
                "md5": "aaca7ef067dcab7cb8d79c36243823e4",
                "sha256": "ea94ce54261720c16abb508c6dcd1fd481c30c09b7f2f5ab0b79e3199b7e2b55"
            },
            "extra": {
                "last_touched": null,
                "materialized_path": "/Images/23296359282_934200ec59_o.jpg",
                "current_version": 1,
                "provider": "osfstorage",
                "path": "/5cd98518f244ec001ee8606b",
                "current_user_can_comment": true,
                "guid": null,
                "checkout": null,
                "tags": []
            }
        }

        400: Bad Request
        {
            "error": "'new_target' does not support the action 'resource_detail'."
        }
        or
        {
            "error": "'presqt-source-token' missing in the request headers."
        }

        401: Unauthorized
        {
            "error": "Token is invalid. Response returned a 401 status code.""
        }

        403: Forbidden
        {
            "error": "User does not have access to this resource with the token provided."
        }

        404: Not Found
        {
            "error": "'bad_target' is not a valid Target name."
        }
        or
        {
            "error": "Resource with id 'bad_id' not found for this user."
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
        func = FunctionRouter.get_function(target_name, action)

        # Fetch the resource
        try:
            resource = func(token, resource_id)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch
            return Response(data={'error': e.data}, status=e.status_code)

        serializer = ResourceSerializer(instance=resource)
        return Response(serializer.data)


class PrepareDownload(APIView):
    """
    **Supported HTTP Methods**

    * GET: Prepares a download of a resource with the given resource ID provided. Spawns a
    process separate from the request server to do the actual downloading and zip-file preparation.

    """

    def get(self, request, target_name, resource_id):
        """
        Prepare a resource for download.

        Parameters
        ----------
        target_name : str
            The name of the Target resource to retrieve.
        resource_id : str
            The id of the Resource to retrieve.

        Returns
        -------
        FILL IN

        400: Bad Request
        {
            "error": "'new_target' does not support the action 'resource_download'."
        }
        or
        {
            "error": "'presqt-source-token' missing in the request headers."
        }

        # 401: Unauthorized
        # {
        #     "error": "Token is invalid. Response returned a 401 status code.""
        # }

        # 403: Forbidden
        # {
        #     "error": "User does not have access to this resource with the token provided."
        # }

        404: Not Found
        {
            "error": "'bad_target' is not a valid Target name."
        }
        # or
        # {
        #     "error": "Resource with id 'bad_id' not found for this user."
        # }
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

        # Generate ticket number
        ticket_number = uuid4()

        # Create directory and json file
        server_metadata_obj = {
            'presqt-source-token': token,
            'status': 'in_progress',
            'expiration': str(datetime.now() + timedelta(days=5)),
            'kill_time': str(datetime.now() + timedelta(hours=1)),
            'message': None,
            'status_code': None
        }
        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)
        server_metadata_path = '{}/server_metadata.json'.format(ticket_path)
        write_file(server_metadata_path, server_metadata_obj, True)

        # Spawn separate job
        # ¯\_(ツ)_/¯
        # This is current;y working on another thread as were are no longer seeing print statements
        # from the function in our log. Phase 2 will be to figure out how to get return data from this process
        function_thread = multiprocessing.Process(target=temp_function, args=[
            target_name, action, token, resource_id, ticket_path, server_metadata_path])

        print(function_thread)

        # Return response
        return Response(status=status.HTTP_200_OK,
                        data={'ticket_number': ticket_number,
                              'message': 'The server is processing the request.'})


def temp_function(target_name, action, token, resource_id, ticket_path, server_metadata_path):
    # Fetch the proper function to call
    func = FunctionRouter.get_function(target_name, action)

    print('We working')
    # Fetch the resources. 'resources' will be a list  the following dict:
    # {'file': binary_file,
    # 'hashes': {'some_hash': value, 'other_hash': value},
    # 'title': resource_title,
    # 'path': /some/path/to/resource}
    try:
        resources = func(token, resource_id)
    except PresQTResponseException as e:
        # Catch any errors that happen within the target fetch.
        # Update the server metadata file appropriately.
        data = read_file(server_metadata_path, True)
        data['status_code'] = e.status_code
        data['status'] = 'failed'
        data['message'] = e.data
        write_file(server_metadata_path, data, True)
        return

    # The directory all files should be saved in.
    file_name = '{}_download_{}'.format(target_name, resource_id)
    folder_directory = '{}/{}'.format(ticket_path, file_name)

    # Loop through the resources, perform fixity check on each one, and save the file to disk.
    fixity_info = []
    for resource in resources:
        # Perform the fixity check and add extra info to the returned fixity object.
        fixity_obj = fixity.fixity_checker(
            resource['file'], resource['hashes'])
        fixity_obj['resource_title'] = resource['title']
        fixity_obj['path'] = resource['path']
        fixity_info.append(fixity_obj)

        # Save the file to the disk.
        file_path = '{}{}'.format(folder_directory, resource['path'])
        write_file(file_path, resource['file'])

    # Add the fixity file to the disk directory
    file_path = '{}/fixity_info.json'.format(folder_directory)
    write_file(file_path, fixity_info, True)

    # Make a Bagit 'bag' of the resources.
    bagit.make_bag(folder_directory)

    # Zip the Bagit 'bag' to send forward.
    zip_file_path = "{}/{}.zip".format(ticket_path, file_name)
    zip_directory(zip_file_path, folder_directory)

    # Everything was a success so update the server metadata file.
    data = read_file(server_metadata_path, True)
    data['status_code'] = '200'
    data['status'] = 'done'
    data['message'] = 'Download successful'
    write_file(server_metadata_path, data, True)
    print('The job is finished')
    return
