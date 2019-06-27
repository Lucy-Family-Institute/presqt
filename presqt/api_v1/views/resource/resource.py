import multiprocessing
import os
import zipfile
from io import BytesIO
from uuid import uuid4

import bagit
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


from presqt.api_v1.serializers.resource import ResourceSerializer
from presqt.api_v1.utilities import (source_token_validation, target_validation, FunctionRouter,
                                     destination_token_validation, write_file)
from presqt.api_v1.utilities.io.read_file import read_file
from presqt.api_v1.utilities.multiprocess.watchdog import process_watchdog
from presqt.api_v1.utilities.validation.file_validation import file_validation
from presqt.exceptions import PresQTValidationError, PresQTResponseException


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
            "error": "Token is invalid. Response returned a 401 status code."
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

        410: Gone
        {
            "error": "The requested resource is no longer available."
        }
        """
        action = 'resource_detail'

        # Perform token, target, and action validation
        try:
            token = source_token_validation(request)
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

    def post(self, request, target_name, resource_id):
        """
        Upload resources to a specific resource.

        Parameters
        ----------
        target_name : str
            The name of the Target resource to retrieve.
        resource_id : str
            The id of the Resource to retrieve.

        Returns
        -------
        202: Accepted
        {
            "ticket_number": "some_uuid"
            "message": "The server is processing the request."
        }

        400: Bad Request
        {
            "error": "'new_target' does not support the action 'resource_upload'."
        }
        or
        {
            "error": "'presqt-destination-token' missing in the request headers."
        }

        404: Not Found
        {
            "error": "'bad_target' is not a valid Target name."
        }
        """
        action = 'resource_upload'

        # Perform token, target, action, and resource validation
        try:
            token = destination_token_validation(request)
            target_validation(target_name, action)
            resource = file_validation(request)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Generate ticket number
        ticket_number = uuid4()
        ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

        # Extract the zip file to disk
        with zipfile.ZipFile(resource) as myzip:
            myzip.extractall(ticket_path)

        resource_main_dir = '{}/{}'.format(ticket_path, next(os.walk(ticket_path))[1][0])

        # Verify it is BagIt
        bag = bagit.Bag(resource_main_dir)
        # POSSIBLY CREATE A CLEARER EXPLANATION WHY
        if not bag.is_valid(bag):
            return Response(data={'error': 'The file provided is not in BagIt format.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Create directory and write process_info.json file
        process_info_obj = {
            'presqt-destination-token': token,
            'status': 'in_progress',
            'expiration': str(timezone.now() + relativedelta(days=5)),
            'message': 'Upload is being processed on the server',
            'status_code': None
        }
        process_info_path = '{}/process_info.json'.format(ticket_path)
        write_file(process_info_path, process_info_obj, True)

        # Create a shared memory map that the watchdog monitors to see if the spawned
        # off process has finished
        process_state = multiprocessing.Value('b', 0)
        # Spawn job separate from request memory thread
        function_process = multiprocessing.Process(target=upload_resource,
                                                   args=[resource_main_dir, process_info_path, bag.payload_entries(), target_name, action, token, resource_id, process_state])
        function_process.start()

        # Start the watchdog process that will monitor the spawned off process
        watch_dog = multiprocessing.Process(target=process_watchdog,
                                            args=[function_process, process_info_path, 3600,
                                                  process_state])
        watch_dog.start()

        return Response(status=status.HTTP_202_ACCEPTED,
                        data={'ticket_number': ticket_number,
                              'message': 'The server is processing the request.'})

def upload_resource(resource_main_dir, process_info_path, bag_payload_entries, target_name, action, token, resource_id, process_state):
    # Fetch the proper function to call
    func = FunctionRouter.get_function(target_name, action)

    # Get the current process_info.json data to be used throughout the file
    process_info_data = read_file(process_info_path, True)

    # Upload the resources
    try:
        uploaded_resources = func(token, resource_id, resource_main_dir)
    except PresQTResponseException as e:
        # Catch any errors that happen within the target fetch.
        # Update the server process_info file appropriately.
        process_info_data['status_code'] = e.status_code
        process_info_data['status'] = 'failed'
        process_info_data['message'] = e.data
        # Update the expiration from 5 days to 1 hour from now. We can delete this faster because
        # it's an incomplete/failed directory.
        process_info_data['expiration'] = str(timezone.now() + relativedelta(hours=1))
        write_file(process_info_path, process_info_data, True)
        #  Update the shared memory map so the watchdog process can stop running.
        process_state.value = 1
        return

    # Everything was a success so update the server metadata file.
    process_info_data['status_code'] = '200'
    process_info_data['status'] = 'finished'
    process_info_data['message'] = 'Upload successful'
    write_file(process_info_path, process_info_data, True)

    # Update the shared memory map so the watchdog process can stop running.
    process_state.value = 1
    return
