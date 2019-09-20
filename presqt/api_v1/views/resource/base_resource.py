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
                                     file_duplicate_action_validation, FunctionRouter,
                                     get_source_token, transfer_post_body_validation,
                                     spawn_action_process, get_or_create_hashes_from_bag)
from presqt.api_v1.utilities.fixity import download_fixity_checker
from presqt.api_v1.utilities.validation.bagit_validation import validate_bag
from presqt.api_v1.utilities.validation.file_validation import file_validation
from presqt.utilities import (PresQTValidationError, PresQTResponseException, write_file,
                              zip_directory)


class BaseResource(APIView):
    """
    Base View for Resource views. Handles shared POSTs (upload and transfer) and download methods.
    """
    def post(self, request, target_name, resource_id=None):
        """
        Upload resources to a specific resource or create a new resource.

        Parameters
        ----------
        request : HTTP Request Object
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
        or
        {
        "error": "source_resource_id can't be None or blank."
        }
        or
        {
        "error": "source_resource_id was not found in the request body."
        }
        or
        {
        "error": "source_target_name was not found in the request body."
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
        # Set class attributes that are used in POST methods
        self.request = request
        self.destination_target_name = target_name
        self.destination_resource_id = resource_id

        # Route to upload POST method
        if request.FILES:
            self.action = 'resource_upload'
            return self.upload_post()
        # Route to transfer POST method
        else:
            self.action = 'resource_transfer'
            return self.transfer_post()

    def upload_post(self):
        """
        Upload resources to a specific existing target resource or create a new target resource.

        Returns
        -------
        Response object in JSON format
        """
        # Perform token, header, target, action, and resource validation
        try:
            self.destination_token = get_destination_token(self.request)
            self.file_duplicate_action = file_duplicate_action_validation(self.request)
            target_validation(self.destination_target_name, self.action)
            resource = file_validation(self.request)
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

            self.resource_main_dir = '{}/{}'.format(ticket_path, next(os.walk(ticket_path))[1][0])

            # Validate the 'bag' and check for checksum mismatches
            bag = bagit.Bag(self.resource_main_dir)
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
        self.process_info_obj = {
            'presqt-destination-token': self.destination_token,
            'status': 'in_progress',
            'expiration': str(timezone.now() + relativedelta(days=5)),
            'message': 'Upload is being processed on the server',
            'status_code': None
        }

        self.process_info_path = '{}/process_info.json'.format(ticket_path)
        write_file(self.process_info_path, self.process_info_obj, True)

        # Create a hash dictionary to compare with the hashes returned from the target after upload
        # If the destination target supports a hash provided by the bag then use those hashes
        # otherwise create new hashes with a target supported hash.
        self.file_hashes, self.hash_algorithm = get_or_create_hashes_from_bag(self, bag)

        # Spawn the upload_resource method separate from the request server by using multiprocess.
        spawn_action_process(self, self._upload_resource)

        reversed_url = reverse('upload_job', kwargs={'ticket_number': ticket_number})
        upload_hyperlink = self.request.build_absolute_uri(reversed_url)

        return Response(status=status.HTTP_202_ACCEPTED,
                        data={'ticket_number': ticket_number,
                              'message': 'The server is processing the request.',
                              'upload_job': upload_hyperlink})

    def _download_resource(self):
        """
        Downloads the resources from the target, performs a fixity check,
        zips them up in BagIt format.
        """
        action = 'resource_download'

        # Fetch the proper function to call
        func = FunctionRouter.get_function(self.source_target_name, action)

        # Fetch the resources. 'resources' will be a list of the following dictionary:
        # {'file': binary_file,
        # 'hashes': {'some_hash': value, 'other_hash': value},
        # 'title': resource_title,
        # 'path': /some/path/to/resource}
        try:
            resources, empty_containers = func(self.source_token, self.source_resource_id)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch.
            # Update the server process_info file appropriately.
            self.process_info_obj['status_code'] = e.status_code
            self.process_info_obj['status'] = 'failed'
            self.process_info_obj['message'] = e.data
            # Update the expiration from 5 days to 1 hour from now. We can delete this faster because
            # it's an incomplete/failed directory.
            self.process_info_obj['expiration'] = str(timezone.now() + relativedelta(hours=1))
            write_file(self.process_info_path, self.process_info_obj, True)
            #  Update the shared memory map so the watchdog process can stop running.
            self.process_state.value = 1
            return False

        # The directory all files should be saved in.
        self.resource_main_dir = '{}/{}'.format(self.ticket_path, self.base_directory_name)

        # For each resource, perform fixity check, and save to disk.
        fixity_info = []
        self.fixity_match = True
        for resource in resources:
            # Perform the fixity check and add extra info to the returned fixity object.
            fixity_obj, self.fixity_match = download_fixity_checker.download_fixity_checker(
                resource['file'], resource['hashes'])
            fixity_obj['resource_title'] = resource['title']
            fixity_obj['path'] = resource['path']
            fixity_info.append(fixity_obj)

            # Save the file to the disk.
            write_file('{}{}'.format(self.resource_main_dir, resource['path']), resource['file'])

        # Write empty containers to disk
        for container_path in empty_containers:
            # Make sure the container_path has a '/' and the beginning and end
            if container_path[-1] != '/':
                container_path += '/'
            if container_path[0] != '/':
                container_path = '/' + container_path

            os.makedirs(os.path.dirname('{}{}'.format(self.resource_main_dir, container_path)))

        if self.fixity_match is True:
            self.process_info_obj['message'] = 'Download successful'
        else:
            self.process_info_obj['message'] = 'Download successful with fixity errors'

        # If we are transferring the downloaded resource then bag it for the resource_upload method
        if self.action == 'resource_transfer':
            # Make a BagIt 'bag' of the resources.
            bagit.make_bag(self.resource_main_dir, checksums=['md5', 'sha1', 'sha256', 'sha512'])
            self.process_info_obj['download_status'] = self.process_info_obj['message']
            return True

        # If we are only downloading the resource then bag, zip it, update the server process file
        else:
            # Add the fixity file to the disk directory
            write_file('{}/fixity_info.json'.format(self.resource_main_dir), fixity_info, True)

            # Make a BagIt 'bag' of the resources.
            bagit.make_bag(self.resource_main_dir, checksums=['md5', 'sha1', 'sha256', 'sha512'])

            # Zip the BagIt 'bag' to send forward.
            zip_directory(self.resource_main_dir, "{}.zip".format(self.resource_main_dir),
                          self.ticket_path)

            # Everything was a success so update the server metadata file.
            self.process_info_obj['status_code'] = '200'
            self.process_info_obj['status'] = 'finished'
            self.process_info_obj['zip_name'] = '{}.zip'.format(self.base_directory_name)
            write_file(self.process_info_path, self.process_info_obj, True)

            # Update the shared memory map so the watchdog process can stop running.
            self.process_state.value = 1
            return True

    def _upload_resource(self):
        """
        Upload resources to the target and perform a fixity check on the resulting hashes.
        """
        action = 'resource_upload'

        # Data directory in the bag
        data_directory = '{}/data'.format(self.resource_main_dir)

        # Fetch the proper function to call
        func = FunctionRouter.get_function(self.destination_target_name, action)

        # Upload the resources
        # 'uploaded_file_hashes' should be a dictionary of files and their hashes according to the
        # hash_algorithm we are using. For example, if hash_algorithm == sha256:
        #     {'mediafiles/uploads/66e7b906-63f0/osf_download_5cd98b0af244/data/fixity_info.json':
        #         'a48df41bb55c7f9e1fa41b02197477ff0eccb550ed1244155048ef5750993ce7',
        #     'mediafiles/uploads/66e7b906-63f0/osf_download_5cd98b0af244e/data/Docs2/02.mp3':
        #         'fe3e904fbd549a3ac014bc26fb3d5042d58759f639f24e745dba3580ea316850'
        #     }
        # 'resources_ignored' is list of paths of resources that were ignored while uploading
        # 'resources_updated' is list of paths of resources that were updated while uploading
        try:
            uploaded_file_hashes, resources_ignored, resources_updated = func(
                self.destination_token, self.destination_resource_id, data_directory,
                self.hash_algorithm, self.file_duplicate_action)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch.
            # Update the server process_info file appropriately.
            self.process_info_obj['status_code'] = e.status_code
            self.process_info_obj['status'] = 'failed'
            self.process_info_obj['message'] = e.data
            # Update the expiration from 5 days to 1 hour from now. We can delete this faster because
            # it's an incomplete/failed directory.
            self.process_info_obj['expiration'] = str(timezone.now() + relativedelta(hours=1))
            write_file(self.process_info_path, self.process_info_obj, True)
            #  Update the shared memory map so the watchdog process can stop running.
            self.process_state.value = 1
            return False

        # Check if fixity fails on any files. If so, then update the process_info_data file.
        self.process_info_obj['failed_fixity'] = []
        if self.file_hashes != uploaded_file_hashes:
            self.process_info_obj['message'] = 'Upload successful but fixity failed.'
            for key, value in self.file_hashes.items():
                if value != uploaded_file_hashes[key] and key not in resources_ignored:
                    self.process_info_obj['failed_fixity'].append(key[len(data_directory)+1:])
        else:
            self.process_info_obj['message'] = 'Upload successful'

        # Strip the server created directory prefix of the file paths for ignored and updated files
        self.process_info_obj['resources_ignored'] = [file[len(data_directory)+1:]
                                                            for file in resources_ignored]
        self.process_info_obj['resources_updated'] = [file[len(data_directory)+1:]
                                                            for file in resources_updated]

        # If we are uploading only and not transferring then update the server process file
        if self.action == 'resource_upload':
            self.process_info_obj['status_code'] = '200'
            self.process_info_obj['status'] = 'finished'
            self.process_info_obj['hash_algorithm'] = self.hash_algorithm
            write_file(self.process_info_path, self.process_info_obj, True)

            # Update the shared memory map so the watchdog process can stop running.
            self.process_state.value = 1
        else:
            self.process_info_obj['upload_status'] = self.process_info_obj['message']

        return True

    def transfer_post(self):
        """
        Transfer resources to a specific existing target resource or create a new target resource.

        Returns
        -------
        Response object in JSON format
        """
        try:
            self.destination_token = get_destination_token(self.request)
            self.source_token = get_source_token(self.request)
            self.file_duplicate_action = file_duplicate_action_validation(self.request)
            self.source_target_name, self.source_resource_id = transfer_post_body_validation(self.request)
            target_validation(self.destination_target_name, self.action)
            target_validation(self.source_target_name, self.action)
            ############# VALIDATION TO ADD #############
            # CHECK THAT source_target_name CAN TRANSFER TO destination_target_name
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Generate ticket number
        ticket_number = uuid4()
        self.ticket_path = 'mediafiles/transfers/{}'.format(ticket_number)

        # Create directory and process_info json file
        self.process_info_obj = {
            'presqt-source-token': self.source_token,
            'presqt-destination-token': self.destination_token,
            'status': 'in_progress',
            'expiration': str(timezone.now() + relativedelta(days=5)),
            'message': 'Transfer is being processed on the server',
            'status_code': None
        }
        self.process_info_path = '{}/process_info.json'.format(self.ticket_path)
        write_file(self.process_info_path, self.process_info_obj, True)

        self.base_directory_name = '{}_{}_transfer_{}'.format(self.source_target_name,
                                                    self.destination_target_name,
                                                    self.source_resource_id)

        # Spawn the transfer_resource method separate from the request server by using multiprocess.
        spawn_action_process(self, self._transfer_resource)

        reversed_url = reverse('transfer_job', kwargs={'ticket_number': ticket_number})
        transfer_hyperlink = self.request.build_absolute_uri(reversed_url)

        return Response(status=status.HTTP_202_ACCEPTED,
                        data={'ticket_number': ticket_number,
                              'message': 'The server is processing the request.',
                              'transfer_job': transfer_hyperlink})

    def _transfer_resource(self):
        """
        Transfer resources from the source target to the destination target.
        """
        ####### DOWNLOAD THE RESOURCES #######
        download_status = self._download_resource()

        # If download failed then don't continue
        if not download_status:
            return

        ####### PREPARE UPLOAD FROM DOWNLOAD BAG #######
        # Validate the 'bag' and check for checksum mismatches
        bag = bagit.Bag(self.resource_main_dir)
        try:
            validate_bag(bag)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Create a hash dictionary to compare with the hashes returned from the target after upload
        # If the destination target supports a hash provided by the bag then use those hashes,
        # otherwise create new hashes with a target supported hash.
        self.file_hashes, self.hash_algorithm = get_or_create_hashes_from_bag(self, bag)

        ####### UPLOAD THE RESOURCES #######
        upload_status = self._upload_resource()

        # If upload failed then don't continue
        if not upload_status:
            return

        ####### TRANSFER COMPLETE #######
        # Transfer was a success so update the server metadata file.
        self.process_info_obj['status_code'] = '200'
        self.process_info_obj['status'] = 'finished'
        if self.fixity_match is True:
            self.process_info_obj['message'] = 'Transfer successful'
        else:
            self.process_info_obj['message'] = 'Transfer successful with fixity errors'
        write_file(self.process_info_path, self.process_info_obj, True)

        # Update the shared memory map so the watchdog process can stop running.
        self.process_state.value = 1
        return

