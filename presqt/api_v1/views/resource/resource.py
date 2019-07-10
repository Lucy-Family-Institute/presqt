import multiprocessing
import os
import shutil
import zipfile
from uuid import uuid4

import bagit
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from presqt.api_v1.serializers.resource import ResourceSerializer
from presqt.api_v1.utilities import (source_token_validation, target_validation, FunctionRouter,
                                     write_file, destination_token_validation, read_file,
                                     zip_directory, get_target_data, hash_generator, fixity_checker,
                                     file_duplicate_action_validation)
from presqt.api_v1.utilities.io.remove_path_contents import remove_path_contents
from presqt.api_v1.utilities.multiprocess.watchdog import process_watchdog
from presqt.api_v1.utilities.validation.bagit_validation import validate_bag
from presqt.api_v1.utilities.validation.file_validation import file_validation
from presqt.exceptions import PresQTValidationError, PresQTResponseException


class Resource(APIView):
    """
    **Supported HTTP Methods**

    * GET:
        - Retrieve a summary of the resource for the given Target that has been requested.
        or
        - Retrieve a Zip file of the resource and prepare the download of it.
    """
    required_scopes = ['read']

    def get(self, request, target_name, resource_id, resource_format):
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
            }
        }

        202: Accepted
        'zip' format success response.
        {
            "ticket_number": "1234567890"
            "message": "The server is processing the request."
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
        if resource_format == 'json':
            return self.get_json_format(request, target_name, resource_id)
        elif resource_format == 'zip':
            return self.get_zip_format(request, target_name, resource_id)
        else:
            return Response(
                data={
                    'error': '{} is not a valid format for this endpoint.'.format(resource_format)},
                status=status.HTTP_400_BAD_REQUEST)

    def get_json_format(self, request, target_name, resource_id):
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

        serializer = ResourceSerializer(instance=resource)
        return Response(serializer.data)

    def get_zip_format(self, request, target_name, resource_id):
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
        function_process = multiprocessing.Process(target=download_resource, args=[
            target_name, action, token, resource_id, ticket_path, process_info_path, process_state])
        function_process.start()

        # Start the watchdog process that will monitor the spawned off process
        watch_dog = multiprocessing.Process(target=process_watchdog,
                                            args=[function_process, process_info_path,
                                                  3600, process_state])
        watch_dog.start()

        # Get the download url
        reversed_url = reverse('download_resource', kwargs={'ticket_number': ticket_number})
        download_hyperlink = request.build_absolute_uri(reversed_url)

        return Response(status=status.HTTP_202_ACCEPTED,
                        data={'ticket_number': ticket_number,
                              'message': 'The server is processing the request.',
                              'download_link': download_hyperlink})

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
        or
        {
            "error": "The file, 'presqt-file', is not found in the body of the request."
        }
        or
        {
            "error": "The file provided, 'presqt-file', is not a zip file."
        }
        o"
        {
            "error": "The file provided is not in BagIt format."
        }
        or
        {
            "error": "Checksums failed to validate."
        }
        or
        {
            "error": "'presqt-file-duplicate-action' missing in the request headers."
        }
        or
        {
            "error": "'bad_action' is not a valid file_duplicate_action.
            The options are 'ignore' or 'update'."
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
        action = 'resource_upload'

        # Perform token, header, target, action, and resource validation
        try:
            token = destination_token_validation(request)
            file_duplicate_action = file_duplicate_action_validation(request)
            target_validation(target_name, action)
            resource = file_validation(request)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Save the files to disk and check their fixity integrity. If BagIt validation fails attempt
        # to save files to disk again. If BagIt validation fails after 3 attempts return an error.
        upload_fixity = False
        upload_attempts = 0
        while not upload_fixity:
            # Generate ticket number
            ticket_number = uuid4()
            ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

            # Extract each file in the zip file to disk and check for fixity
            with zipfile.ZipFile(resource) as myzip:
                myzip.extractall(ticket_path)

            resource_main_dir = '{}/{}'.format(ticket_path, next(os.walk(ticket_path))[1][0])

            # Validate the 'bag' and check for checksum mismatches
            bag = bagit.Bag(resource_main_dir)
            try:
                validate_bag(bag)
            except PresQTValidationError as e:
                upload_attempts += 1
                shutil.rmtree(ticket_path)
                if upload_attempts > 2:
                    return Response(data={'error': e.data}, status=e.status_code)
            else:
                upload_fixity = True

        # Create a hash dictionary to compare with the hashes returned from the target after upload
        file_hashes = {}
        # Check if the hash algorithms provided in the bag are supported by the target
        target_supported_algorithms = get_target_data(target_name)['supported_hash_algorithms']
        matched_algorithms = set(target_supported_algorithms).intersection(bag.algorithms)
        # If the bag and target have a matching supported hash algorithm then pull that algorithm's
        # hash from the bag.
        # Else calculate a new hash for each file with a target supported hash algorithm.
        if matched_algorithms:
            hash_algorithm = matched_algorithms.pop()
            for key, value in bag.payload_entries().items():
                file_hashes['{}/{}'.format(resource_main_dir, key)] = value[hash_algorithm]
        else:
            hash_algorithm = target_supported_algorithms[0]
            for key, value in bag.payload_entries().items():
                file_path = '{}/{}'.format(resource_main_dir, key)
                binary_file = read_file(file_path)
                file_hashes[file_path] = hash_generator(binary_file, hash_algorithm)

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
                                                   args=[resource_main_dir, process_info_path,
                                                         target_name, action, token, resource_id,
                                                         process_state, hash_algorithm,
                                                         file_hashes, file_duplicate_action])
        function_process.start()

        # Start the watchdog process that will monitor the spawned off process
        watch_dog = multiprocessing.Process(target=process_watchdog,
                                            args=[function_process, process_info_path, 3600,
                                                  process_state])
        watch_dog.start()

        return Response(status=status.HTTP_202_ACCEPTED,
                        data={'ticket_number': ticket_number,
                              'message': 'The server is processing the request.'})


def download_resource(target_name, action, token, resource_id, ticket_path,
                      process_info_path, process_state):
    """
    Downloads the resources from the target, performs a fixity check, zips them up in BagIt format.

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
        fixity_obj = fixity_checker(
            resource['file'], resource['hashes'])
        fixity_obj['resource_title'] = resource['title']
        fixity_obj['path'] = resource['path']
        fixity_info.append(fixity_obj)

        # Save the file to the disk.
        write_file('{}{}'.format(base_directory, resource['path']), resource['file'])

    # Add the fixity file to the disk directory
    write_file('{}/fixity_info.json'.format(base_directory), fixity_info, True)

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

def upload_resource(resource_main_dir, process_info_path, target_name, action, token, resource_id,
                    process_state, hash_algorithm, file_hashes, file_duplicate_action):
    """
    Upload resources to the target and perform a fixity check on the resulting hashes.

    Parameters
    ----------
    resource_main_dir : str
        Path to the main directory for the resources to be uploaded.
    process_info_path : str
        Path to the process_info JSON file.
    target_name : str
        Name of the Target resource to retrieve.
    action : str
        Name of the action being performed.
    token : str
        Token of the user performing the request.
    resource_id: str
        ID of the Resource to retrieve.
    process_state : memory_map object
        Shared memory map object that the watchdog process will monitor.
    hash_algorithm : str
        Hash algorithm we are using to check for fixity.
    file_hashes : dict
        Dictionary of the file hashes obtained from the bag's manifest
    file_duplicate_action : str
        Action for how to handle any duplicate files we find.
    """
    # Fetch the proper function to call
    func = FunctionRouter.get_function(target_name, action)

    # Get the current process_info.json data to be used throughout the file
    process_info_data = read_file(process_info_path, True)

    # Data directory in the bag
    data_directory = '{}/data'.format(resource_main_dir)

    # Upload the resources
    # 'uploaded_file_hashes' should be a dictionary of files and their hashes according to the
    # hash_algorithm we are using. For example if hash_algorithm == sha256:
    #     {'mediafiles/uploads/66e7b906-63f0-4160-/osf_download_5cd98b0af244/data/fixity_info.json':
    #         'a48df41bb55c7f9e1fa41b02197477ff0eccb550ed1244155048ef5750993ce7',
    #     'mediafiles/uploads/66e7b906-63f0-4160-b20d/osf_download_5cd98b0af244e/data/Docs2/02.mp3':
    #         'fe3e904fbd549a3ac014bc26fb3d5042d58759f639f24e745dba3580ea316850'
    #     }
    # 'files_ignored' should be a list of file paths of files that were ignored while uploading
    # 'files_updated' should be a list of file paths of files that were updated while uploading
    try:
        uploaded_file_hashes, files_ignored, files_updated = func(
            token, resource_id, data_directory, hash_algorithm, file_duplicate_action)
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
    process_info_data['failed_fixity'] = []
    process_info_data['duplicate_files_ignored'] = []
    process_info_data['duplicate_files_updated'] = []
    process_info_data['message'] = 'Upload successful'
    process_info_data['hash_algorithm'] = hash_algorithm

    # Check if fixity fails on any files. If so, then update the process_info_data file.
    if file_hashes != uploaded_file_hashes:
        process_info_data['message'] = 'Upload successful but fixity failed.'
        for key, value in file_hashes.items():
            if value != uploaded_file_hashes[key] and key not in files_ignored:
                process_info_data['failed_fixity'].append(key[len(resource_main_dir)+1:])

    # Strip the server created directory prefix of the file paths for ignored and updated files
    for file_path in files_ignored:
        process_info_data['duplicate_files_ignored'].append(file_path[len(resource_main_dir)+1:])
    for file_path in files_updated:
        process_info_data['duplicate_files_updated'].append(file_path[len(resource_main_dir)+1:])

    write_file(process_info_path, process_info_data, True)

    # Update the shared memory map so the watchdog process can stop running.
    process_state.value = 1
    print('DONE')
    return
