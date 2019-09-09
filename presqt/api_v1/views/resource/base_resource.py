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

from presqt.api_v1.utilities import (target_validation, get_destination_token,
                                     get_target_data, hash_generator,
                                     file_duplicate_action_validation, FunctionRouter,
                                     get_source_token, transfer_post_body_validation)
from presqt.api_v1.utilities.fixity import download_fixity_checker
from presqt.api_v1.utilities.multiprocess.watchdog import process_watchdog
from presqt.api_v1.utilities.validation.bagit_validation import validate_bag
from presqt.api_v1.utilities.validation.file_validation import file_validation
from presqt.utilities import (PresQTValidationError, PresQTResponseException, read_file, write_file,
                              list_intersection)


class BaseResource(APIView):
    """
    Base View for Resource detail and collection views. Handles shared POST and upload methods.
    """
    def post(self, request, target_name, resource_id=None):
        """
        Upload resources to a specific resource or create a new resource.

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
        or
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
        or
        {
            "error": "Project is not formatted correctly. Multiple directories
            exist at the top level."
        }
        or
        {
            "error": "Project is not formatted correctly. Files exist at the top level."
        }

        401: Unauthorized
        {
            "error": "Token is invalid. Response returned a 401 status code."
        {

        403: Forbidden
        {
            "error": "User does not have access to this resource with the token provided."
        }

        404: Not Found
        {
            "error": "'bad_name' is not a valid Target name."
        }

        410: Not Found
        {
            "error": "The requested resource is no longer available."
        }
        """
        if request.FILES:
            return self.upload_post(request, target_name, resource_id)
        else:
            return self.transfer_post(request, target_name, resource_id)

    def upload_post(self, request, target_name, resource_id):
        """
        Upload resources to a specific existing target resource or create a new target resource.

        Parameters
        ----------
        request : HTTP Request Object
        target_name : str
            The name of the Target to upload to.
        resource_id : str
            The id of the Resource to upload to.

        Returns
        -------
        Response object in JSON format
        """
        action = 'resource_upload'
        # Perform token, header, target, action, and resource validation
        try:
            token = get_destination_token(request)
            file_duplicate_action = file_duplicate_action_validation(request)
            target_validation(target_name, action)
            resource = file_validation(request)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Save files to disk and check their fixity integrity. If BagIt validation fails, attempt
        # to save files to disk again. If BagIt validation fails after 3 attempts return an error.
        for index in range(3):
            # Generate ticket number
            ticket_number = uuid4()
            ticket_path = 'mediafiles/uploads/{}'.format(ticket_number)

            # Extract each file in the zip file to disk
            with zipfile.ZipFile(resource) as myzip:
                myzip.extractall(ticket_path)

            resource_main_dir = '{}/{}'.format(ticket_path, next(os.walk(ticket_path))[1][0])

            # Validate the 'bag' and check for checksum mismatches
            bag = bagit.Bag(resource_main_dir)
            try:
                validate_bag(bag)
            except PresQTValidationError as e:
                shutil.rmtree(ticket_path)
                # If we've reached the maximum number of attempts then return an error response
                if index == 2:
                    return Response(data={'error': e.data}, status=e.status_code)
            else:
                # If the bag validated successfully then break from the loop
                break

        # Write process_info.json file
        process_info_obj = {
            'presqt-destination-token': token,
            'status': 'in_progress',
            'expiration': str(timezone.now() + relativedelta(days=5)),
            'message': 'Upload is being processed on the server',
            'status_code': None
        }
        process_info_path = '{}/process_info.json'.format(ticket_path)
        write_file(process_info_path, process_info_obj, True)

        # Create a hash dictionary to compare with the hashes returned from the target after upload
        file_hashes = {}
        # Check if the hash algorithms provided in the bag are supported by the target
        target_supported_algorithms = get_target_data(target_name)['supported_hash_algorithms']
        matched_algorithms = set(target_supported_algorithms).intersection(bag.algorithms)
        # If the bag and target have a matching supported hash algorithm then pull that algorithm's
        # hash from the bag.
        if matched_algorithms:
            hash_algorithm = matched_algorithms.pop()
            for key, value in bag.payload_entries().items():
                file_hashes['{}/{}'.format(resource_main_dir, key)] = value[hash_algorithm]
        # Else calculate a new hash for each file with a target supported hash algorithm.
        else:
            hash_algorithm = target_supported_algorithms[0]
            for key, value in bag.payload_entries().items():
                file_path = '{}/{}'.format(resource_main_dir, key)
                binary_file = read_file(file_path)
                file_hashes[file_path] = hash_generator(binary_file, hash_algorithm)

        # Create a shared memory map that the watchdog monitors to see if the spawned
        # off process has finished
        process_state = multiprocessing.Value('b', 0)
        # Spawn job separate from request memory thread
        function_process = multiprocessing.Process(target=self._upload_resource,
                                                   args=[resource_main_dir, process_info_path,
                                                         target_name, action, token, resource_id,
                                                         process_state, hash_algorithm, file_hashes,
                                                         file_duplicate_action, process_info_obj])
        function_process.start()

        # Start the watchdog process that will monitor the spawned off process
        watch_dog = multiprocessing.Process(target=process_watchdog,
                                            args=[function_process, process_info_path, 3600,
                                                  process_state])
        watch_dog.start()

        reversed_url = reverse('upload_job', kwargs={'ticket_number': ticket_number})
        upload_hyperlink = request.build_absolute_uri(reversed_url)

        return Response(status=status.HTTP_202_ACCEPTED,
                        data={'ticket_number': ticket_number,
                              'message': 'The server is processing the request.',
                              'upload_job': upload_hyperlink})

    @staticmethod
    def _upload_resource(resource_main_dir, process_info_path, target_name, action, token,
                         resource_id, process_state, hash_algorithm, file_hashes,
                         file_duplicate_action, process_info_data):
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
        process_info_data : dict
            Data currently in the process_info.json
        """
        # Data directory in the bag
        data_directory = '{}/data'.format(resource_main_dir)

        # Fetch the proper function to call
        func = FunctionRouter.get_function(target_name, action)

        # Upload the resources
        # 'uploaded_file_hashes' should be a dictionary of files and their hashes according to the
        # hash_algorithm we are using. For example, if hash_algorithm == sha256:
        #     {'mediafiles/uploads/66e7b906-63f0/osf_download_5cd98b0af244/data/fixity_info.json':
        #         'a48df41bb55c7f9e1fa41b02197477ff0eccb550ed1244155048ef5750993ce7',
        #     'mediafiles/uploads/66e7b906-63f0/osf_download_5cd98b0af244e/data/Docs2/02.mp3':
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
        for file in files_ignored:
            process_info_data['duplicate_files_ignored'].append(file[len(resource_main_dir)+1:])
        for file in files_updated:
            process_info_data['duplicate_files_updated'].append(file[len(resource_main_dir)+1:])

        write_file(process_info_path, process_info_data, True)

        # Update the shared memory map so the watchdog process can stop running.
        process_state.value = 1
        return

    def transfer_post(self, request, destination_target_name, destination_resource_id):
        """
        Transfer resources to a specific existing target resource or create a new target resource.

        Parameters
        ----------
        request : HTTP Request Object
        destination_target_name : str
            The name of the Target to transfer to.
        destination_resource_id : str
            The id of the Resource to upload to.

        Returns
        -------
        Response object in JSON format
        """
        action = 'resource_transfer'
        try:
            destination_token = get_destination_token(request)
            source_token = get_source_token(request)
            file_duplicate_action = file_duplicate_action_validation(request)
            ############# ADD transfer_post_body_validation errors to docsting! #############
            source_target_name, source_resource_id = transfer_post_body_validation(request)
            target_validation(destination_target_name, action)
            target_validation(source_target_name, action)
            ############# VALIDATION TO ADD #############
            # CHECK THAT source_target_name CAN TRANSFER TO destination_target_name
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Generate ticket number
        ticket_number = uuid4()

        # Create directory and process_info json file
        process_info_obj = {
            'presqt-source-token': source_token,
            'presqt-destination-token': destination_token,
            'status': 'in_progress',
            'expiration': str(timezone.now() + relativedelta(days=5)),
            'message': 'Transfer is being processed on the server',
            'status_code': None
        }
        ticket_path = 'mediafiles/transfers/{}'.format(ticket_number)
        process_info_path = '{}/process_info.json'.format(ticket_path)
        write_file(process_info_path, process_info_obj, True)

        # Create a shared memory map that the watchdog monitors to see if the spawned
        # off process has finished
        process_state = multiprocessing.Value('b', 0)
        # Spawn job separate from request memory thread
        function_process = multiprocessing.Process(target=self._transfer_resource,
                                                   args=[source_target_name, source_token,
                                                         source_resource_id,
                                                         destination_target_name, destination_token,
                                                         destination_resource_id, process_info_path,
                                                         process_state, ticket_path,
                                                         file_duplicate_action])
        function_process.start()

        # Start the watchdog process that will monitor the spawned off process
        watch_dog = multiprocessing.Process(target=process_watchdog,
                                            args=[function_process, process_info_path,
                                                  3600, process_state])
        watch_dog.start()

        reversed_url = reverse('transfer_job', kwargs={'ticket_number': ticket_number})
        transfer_hyperlink = request.build_absolute_uri(reversed_url)

        return Response(status=status.HTTP_202_ACCEPTED,
                        data={'ticket_number': ticket_number,
                              'message': 'The server is processing the request.',
                              'transfer_job': transfer_hyperlink})

    @staticmethod
    def _transfer_resource(source_target_name, source_token, source_resource_id,
                           destination_target_name, destination_token, destination_resource_id,
                           process_info_path, process_state, ticket_path, file_duplicate_action):
        """
        Transfer resources from the source target to the destination target.

        Parameters
        ----------
        source_target_name : str
            Name of the target to transfer from
        source_token : str
            User's token for the source target
        source_resource_id : str
            Id of the resource to transfer
        destination_target_name : str
            Name of the target to transfer to
        destination_token : str
            User's token for the destination target
        destination_resource_id : str
            Id of the resource to transfer to
        process_info_path : str
            Path to the process info file
        process_state : memory_map object
            Shared memory map object that the watchdog process will monitor.
        ticket_path: str
            Path to the ticket directory for the resource being transferred.
        file_duplicate_action : str
            Action for how to handle any duplicate files we find.
        """
        ### DOWNLOAD THE RESOURCES ###
        # Fetch the proper download function to call
        download_func = FunctionRouter.get_function(source_target_name, 'resource_download')

        # Get the current process_info.json data to be used throughout the file
        process_info_data = read_file(process_info_path, True)

        # Fetch the resources. 'resources' will be a list of the following dictionary:
        # {'file': binary_file,
        # 'hashes': {'some_hash': value, 'other_hash': value},
        # 'title': resource_title,
        # 'path': /some/path/to/resource}
        try:
            resources, empty_containers = download_func(source_token, source_resource_id)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch. Update server process_info file.
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
        base_directory_name = '{}_{}_transfer_{}'.format(source_target_name,
                                                    destination_target_name,
                                                    source_resource_id)
        base_directory = '{}/{}'.format(ticket_path, base_directory_name)

        # For each resource, perform fixity check, and save to disk.
        fixity_failed = []
        fixity_match = True
        # Keep track of the file hashes using a destination supported hash algorithm
        file_hashes = {}
        destination_target_supported_algorithms = get_target_data(destination_target_name)['supported_hash_algorithms']
        source_target_supported_algorithms = get_target_data(source_target_name)['supported_hash_algorithms']
        try:
            shared_hash_algorithm = list_intersection(destination_target_supported_algorithms, source_target_supported_algorithms)[0]
        except KeyError:
            shared_hash_algorithm = destination_target_supported_algorithms[0]

        for resource in resources:
            resource_path = '{}{}'.format(base_directory, resource['path'])
            # Perform the fixity check and add extra info to the returned fixity object.
            fixity_obj, fixity_match = download_fixity_checker.download_fixity_checker(
                resource['file'], resource['hashes'])
            if not fixity_match:
                fixity_failed.append(resource.path)

            # Save the current hash to be compared with the hashes after upload
            if shared_hash_algorithm == fixity_obj['hash_algorithm']:
                file_hashes[resource_path] = fixity_obj['presqt_hash']
            else:
                file_hashes[resource_path] = hash_generator(resource['file'], shared_hash_algorithm)

            # Save the file to the disk.
            write_file(resource_path, resource['file'])

        # Write empty containers to disk
        for container_path in empty_containers:
            # Make sure the container_path has a '/' and the beginning and end
            if container_path[-1] != '/':
                container_path += '/'
            if container_path[0] != '/':
                container_path = '/' + container_path

            os.makedirs(os.path.dirname('{}{}'.format(base_directory, container_path)))

        ### UPLOAD THE RESOURCES ###
        # Fetch the proper function to call
        upload_func = FunctionRouter.get_function(destination_target_name, 'resource_upload')

        # Upload the resources
        # 'uploaded_file_hashes' should be a dictionary of files and their hashes according to the
        # hash_algorithm we are using. For example, if hash_algorithm == sha256:
        #     {'mediafiles/uploads/66e7b906-63f0/osf_download_5cd98b0af244/data/fixity_info.json':
        #         'a48df41bb55c7f9e1fa41b02197477ff0eccb550ed1244155048ef5750993ce7',
        #     'mediafiles/uploads/66e7b906-63f0/osf_download_5cd98b0af244e/data/Docs2/02.mp3':
        #         'fe3e904fbd549a3ac014bc26fb3d5042d58759f639f24e745dba3580ea316850'
        #     }
        # 'files_ignored' should be a list of file paths of files that were ignored while uploading
        # 'files_updated' should be a list of file paths of files that were updated while uploading
        try:
            uploaded_file_hashes, files_ignored, files_updated = upload_func(
                destination_token, destination_resource_id, base_directory, shared_hash_algorithm,
                file_duplicate_action)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch. Update server process_info file.
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

        # Check if fixity fails on any files. If so, then update the process_info_data file.
        process_info_data['failed_fixity'] = []
        if file_hashes != uploaded_file_hashes:
            process_info_data['message'] = 'Upload successful but fixity failed.'
            for key, value in file_hashes.items():
                if value != uploaded_file_hashes[key] and key not in files_ignored:
                    process_info_data['failed_fixity'].append(key[len(base_directory) + 1:])

        # Strip the server created directory prefix of the file paths for ignored and updated files
        process_info_data['duplicate_files_ignored'] = []
        process_info_data['duplicate_files_updated'] = []
        for file in files_ignored:
            process_info_data['duplicate_files_ignored'].append(file[len(base_directory)+1:])
        for file in files_updated:
            process_info_data['duplicate_files_updated'].append(file[len(base_directory)+1:])

        ### TRANSFER COMPLETE ###
        # Everything was a success so update the server metadata file.
        process_info_data['status_code'] = '200'
        process_info_data['status'] = 'finished'
        if fixity_match is True:
            process_info_data['message'] = 'Transfer successful'
        else:
            process_info_data['message'] = 'Transfer successful with fixity errors'
        write_file(process_info_path, process_info_data, True)

        # Update the shared memory map so the watchdog process can stop running.
        process_state.value = 1
        return