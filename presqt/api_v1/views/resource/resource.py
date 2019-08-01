import multiprocessing
from uuid import uuid4

import bagit
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.reverse import reverse

from presqt.api_v1.serializers.resource import ResourceSerializer
from presqt.api_v1.utilities import (source_token_validation, target_validation, FunctionRouter,
                                     write_file, read_file,
                                     zip_directory)
from presqt.api_v1.utilities.fixity import download_fixity_checker
from presqt.api_v1.utilities.multiprocess.watchdog import process_watchdog
from presqt.api_v1.views.resource.base_resource import BaseResource
from presqt.exceptions import PresQTValidationError, PresQTResponseException


class Resource(BaseResource):
    """
    **Supported HTTP Methods**

    * GET:
        - Retrieve a summary of the resource for the given Target that has been requested.
        or
        - Retrieve a Zip file of the resource and prepare the download of it.
    * POST
        - Upload resources to a given container.
    """
    required_scopes = ['read']

    def get(self, request, target_name, resource_id, resource_format=None):
        """
        Retrieve details about a specific Resource.
        or
        Retrieve a specific Resource in zip format.

        Parameters
        ----------
        target_name : str
            The name of the Target resource to retrieve.
        resource_id : str
            The id of the Resource to retrieve.
        resource_format : str
            The format the Resource detail

        Returns
        -------
        200: OK
        'json' format success response.
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
            },
            "download_url": "http://localhost/api_v1/targets/osf/resources/5cd98518f244ec001ee8606.zip/"
        }

        202: Accepted
        'zip' format success response.
        {
            "ticket_number": "1234567890"
            "message": "The server is processing the request.",
            "download_job": "http://localhost/api_v1/downloads/twqhg1-43r12ewdsqw-1231wq"
        }

        400: Bad Request
        {
            "error": "'new_target' does not support the action 'resource_detail'."
        }
        or
        {
            "error": "'presqt-source-token' missing in the request headers."
        }
        or
        {
            "error": "csv is not a valid format for this endpoint."
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
        if resource_format == 'json' or resource_format is None:
            return self.get_json_format(request, target_name, resource_id)
        elif resource_format == 'zip':
            return self.get_zip_format(request, target_name, resource_id)
        else:
            return Response(
                data={
                    'error': '{} is not a valid format for this endpoint.'.format(resource_format)},
                status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get_json_format(request, target_name, resource_id):
        """
        Retrieve details about a specific Resource.

        Parameters
        ----------
        request : HTTP Request Object
        target_name : str
            The name of the Target resource to retrieve.
        resource_id : str
            The id of the Resource to retrieve.

        Returns
        -------
        Response object in JSON format
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

        serializer = ResourceSerializer(instance=resource, context={
            'target_name': target_name, 'request': request})

        return Response(serializer.data)

    @staticmethod
    def get_zip_format(request, target_name, resource_id):
        """
        Prepares a download of a resource with the given resource ID provided. Spawns a process
        separate from the request server to do the actual downloading and zip-file preparation.

        Parameters
        ----------
        request : HTTP Request Object
        target_name : str
            The name of the Target resource to retrieve.
        resource_id : str
            The id of the Resource to retrieve.

        Returns
        -------
        Response object with ticket information.
        """
        action = 'resource_download'

        # Perform token, target, and action validation
        try:
            token = source_token_validation(request)
            target_validation(target_name, action)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Generate ticket number
        ticket_number = uuid4()

        # Create directory and process_info json file
        process_info_obj = {
            'presqt-source-token': token,
            'status': 'in_progress',
            'expiration': str(timezone.now() + relativedelta(days=5)),
            'message': 'Download is being processed on the server',
            'status_code': None
        }

        ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)
        process_info_path = '{}/process_info.json'.format(ticket_path)
        write_file(process_info_path, process_info_obj, True)
        # Create a shared memory map that the watchdog monitors to see if the spawned
        # off process has finished
        process_state = multiprocessing.Value('b', 0)
        # Spawn job separate from request memory thread
        function_process = multiprocessing.Process(target=Resource._download_resource, args=[
            target_name, action, token, resource_id, ticket_path, process_info_path, process_state])
        function_process.start()
        # Start the watchdog process that will monitor the spawned off process
        watch_dog = multiprocessing.Process(target=process_watchdog,
                                            args=[function_process, process_info_path,
                                                  3600, process_state])
        watch_dog.start()
        # Get the download url
        reversed_url = reverse('download_job', kwargs={'ticket_number': ticket_number})
        download_hyperlink = request.build_absolute_uri(reversed_url)

        return Response(status=status.HTTP_202_ACCEPTED,
                        data={'ticket_number': ticket_number,
                              'message': 'The server is processing the request.',
                              'download_job': download_hyperlink})

    @staticmethod
    def _download_resource(target_name, action, token, resource_id, ticket_path,
                           process_info_path, process_state):
        """
        Downloads the resources from the target, performs a fixity check,
        zips them up in BagIt format.

        Parameters
        ----------
        target_name : str
            Name of the Target resource to retrieve.
        action : str
            Name of the action being performed.
        token : str
            Token of the user performing the request.
        resource_id: str
            ID of the Resource to retrieve.
        ticket_path : str
            Path to the ticket_id directory that holds all downloads and process_info
        process_info_path : str
            Path to the process_info JSON file
        process_state : memory_map object
            Shared memory map object that the watchdog process will monitor
        """
        # Fetch the proper function to call
        func = FunctionRouter.get_function(target_name, action)

        # Get the current process_info.json data to be used throughout the file
        process_info_data = read_file(process_info_path, True)

        # Fetch the resources. 'resources' will be a list of the following dictionary:
        # {'file': binary_file,
        # 'hashes': {'some_hash': value, 'other_hash': value},
        # 'title': resource_title,
        # 'path': /some/path/to/resource}
        try:
            resources = func(token, resource_id)
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
        # The directory all files should be saved in.
        base_file_name = '{}_download_{}'.format(target_name, resource_id)
        base_directory = '{}/{}'.format(ticket_path, base_file_name)

        # For each resource, perform fixity check, and save to disk.
        fixity_info = []
        for resource in resources:
            # Perform the fixity check and add extra info to the returned fixity object.
            fixity_obj = download_fixity_checker.download_fixity_checker(
                resource['file'], resource['hashes'])
            fixity_obj['resource_title'] = resource['title']
            fixity_obj['path'] = resource['path']
            fixity_info.append(fixity_obj)

            # Save the file to the disk.
            write_file('{}{}'.format(base_directory, resource['path']), resource['file'])

        # Add the fixity file to the disk directory
        write_file('{}/fixity_info.json'.format(base_directory),fixity_info, True)

        # Make a BagIt 'bag' of the resources.
        bagit.make_bag(base_directory, checksums=['md5', 'sha1', 'sha256', 'sha512'])

        # Zip the BagIt 'bag' to send forward.
        zip_directory(base_directory, "{}/{}.zip".format(ticket_path, base_file_name), ticket_path)

        # Everything was a success so update the server metadata file.
        process_info_data['status_code'] = '200'
        process_info_data['status'] = 'finished'
        process_info_data['message'] = 'Download successful'
        process_info_data['zip_name'] = '{}.zip'.format(base_file_name)
        write_file(process_info_path, process_info_data, True)

        # Update the shared memory map so the watchdog process can stop running.
        process_state.value = 1
        return
