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
                                     spawn_action_process, get_or_create_hashes_from_bag,
                                     create_fts_metadata, create_download_metadata,
                                     create_upload_transfer_metadata, create_upload_metadata,
                                     get_action_message, get_upload_source_metadata, hash_tokens,
                                     finite_depth_upload_helper)
from presqt.api_v1.utilities.fixity import download_fixity_checker
from presqt.api_v1.utilities.validation.bagit_validation import validate_bag
from presqt.api_v1.utilities.validation.file_validation import file_validation
from presqt.json_schemas.schema_handlers import schema_validator
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
            "ticket_number": "ba025c37-3b33-461c-88a1-659a33f3cf47",
            "message": "The server is processing the request.",
            "upload_job": "https://localhost/api_v1/uploads/ba025c37-3b33-461c-88a1-659a33f3cf47/"
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
            self.action = 'resource_transfer_in'
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
            target_valid, self.infinite_depth = target_validation(
                self.destination_target_name, self.action)
            resource = file_validation(self.request)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Save files to disk and check their fixity integrity. If BagIt validation fails, attempt
        # to save files to disk again. If BagIt validation fails after 3 attempts return an error.
        for index in range(3):
            # Generate ticket number
            ticket_number = uuid4()
            ticket_path = os.path.join("mediafiles", "uploads", str(ticket_number))

            # Extract each file in the zip file to disk
            with zipfile.ZipFile(resource) as myzip:
                myzip.extractall(ticket_path)

            self.resource_main_dir = os.path.join(ticket_path, next(os.walk(ticket_path))[1][0])

            # Validate the 'bag' and check for checksum mismatches
            try:
                bag = bagit.Bag(self.resource_main_dir)
                validate_bag(bag)
            except PresQTValidationError as e:
                shutil.rmtree(ticket_path)
                # If we've reached the maximum number of attempts then return an error response
                if index == 2:
                    return Response(data={'error': e.data}, status=e.status_code)
            except bagit.BagError as e:
                # If we've reached the maximum number of attempts then return an error response
                if index == 2:
                    return Response(data=e.args, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Collect and remove any existing source metadata
                get_upload_source_metadata(self, bag)
                # If the bag validated successfully then break from the loop
                break

        # Write process_info.json file
        self.process_info_obj = {
            'presqt-destination-token': hash_tokens(self.destination_token),
            'status': 'in_progress',
            'expiration': str(timezone.now() + relativedelta(days=5)),
            'message': 'Upload is being processed on the server',
            'status_code': None
        }
        self.process_info_path = os.path.join(ticket_path, 'process_info.json')
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

        # Fetch the resources. func_dict is in the format:
        #   {
        #       'resources': files,
        #       'empty_containers': empty_containers,
        #       'action_metadata': action_metadata
        #   }
        try:
            func_dict = func(self.source_token, self.source_resource_id)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch.
            # Update the server process_info file appropriately.
            self.process_info_obj['status_code'] = e.status_code
            self.process_info_obj['status'] = 'failed'
            if self.action == 'resource_transfer_in':
                self.process_info_obj['download_status'] = 'failed'
            self.process_info_obj['message'] = e.data
            # Update the expiration from 5 days to 1 hour from now. We can delete this faster because
            # it's an incomplete/failed directory.
            self.process_info_obj['expiration'] = str(timezone.now() + relativedelta(hours=1))
            write_file(self.process_info_path, self.process_info_obj, True)
            #  Update the shared memory map so the watchdog process can stop running.
            self.process_state.value = 1
            return False

        # The directory all files should be saved in.
        self.resource_main_dir = os.path.join(self.ticket_path, self.base_directory_name)

        # For each resource, perform fixity check, gather metadata, and save it to disk.
        fixity_info = []
        self.download_fixity = True
        self.source_fts_metadata_actions = []
        self.new_fts_metadata_files = []
        for resource in func_dict['resources']:
            # Perform the fixity check and add extra info to the returned fixity object.
            fixity_obj, self.download_fixity = download_fixity_checker.download_fixity_checker(
                resource)
            fixity_info.append(fixity_obj)

            # Create metadata for this resource. Return True if a valid FTS metadata file is found.
            if create_download_metadata(self, resource, fixity_obj):
                # Don't write valid FTS metadata file.
                continue

            # Save the file to the disk.
            write_file('{}{}'.format(self.resource_main_dir, resource['path']), resource['file'])

        # Create PresQT action metadata
        self.action_metadata = {
            'id': str(uuid4()),
            'actionDateTime': str(timezone.now()),
            'actionType': self.action,
            'sourceTargetName': self.source_target_name,
            'sourceUsername': func_dict['action_metadata']['sourceUsername'],
            'destinationTargetName': 'Local Machine',
            'destinationUsername': None,
            'files': {
                'created': self.new_fts_metadata_files,
                'updated': [],
                'ignored': []
            }
        }

        # Write empty containers to disk
        for container_path in func_dict['empty_containers']:
            # Make sure the container_path has a '/' and the beginning and end
            if container_path[-1] != '/':
                container_path += '/'
            if container_path[0] != '/':
                container_path = '/' + container_path
            os.makedirs(os.path.dirname('{}{}'.format(self.resource_main_dir, container_path)))

        # If we are transferring the downloaded resource then bag it for the resource_upload method
        if self.action == 'resource_transfer_in':
            self.action_metadata['destinationTargetName'] = self.destination_target_name

            # Make a BagIt 'bag' of the resources.
            bagit.make_bag(self.resource_main_dir, checksums=['md5', 'sha1', 'sha256', 'sha512'])
            self.process_info_obj['download_status'] = get_action_message('Download',
                                                                          self.download_fixity, True)
            return True
        # If we are only downloading the resource then create metadata, bag, zip,
        # and update the server process file.
        else:
            # Create and write metadata file.
            final_fts_metadata_data = create_fts_metadata(self.action_metadata,
                                                          self.source_fts_metadata_actions)
            write_file(os.path.join(self.resource_main_dir, 'PRESQT_FTS_METADATA.json'),
                       final_fts_metadata_data, True)

            # Validate the final metadata
            metadata_validation = schema_validator('presqt/json_schemas/metadata_schema.json',
                                                   final_fts_metadata_data)
            self.process_info_obj['message'] = get_action_message('Download', self.download_fixity,
                                                                  metadata_validation)

            # Add the fixity file to the disk directory
            write_file(os.path.join(self.resource_main_dir, 'fixity_info.json'), fixity_info, True)

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
        self.data_directory = '{}/data'.format(self.resource_main_dir)

        if self.infinite_depth is False:
            try:
                finite_depth_upload_helper(self)
            except PresQTResponseException as e:
                # Catch any errors that happen within the target fetch.
                # Update the server process_info file appropriately.
                self.process_info_obj['status_code'] = e.status_code
                self.process_info_obj['status'] = 'failed'
                if self.action == 'resource_transfer_in':
                    self.process_info_obj['upload_status'] = 'failed'
                self.process_info_obj['message'] = e.data
                # Update the expiration from 5 days to 1 hour from now. We can delete this faster because
                # it's an incomplete/failed directory.
                self.process_info_obj['expiration'] = str(timezone.now() + relativedelta(hours=1))
                write_file(self.process_info_path, self.process_info_obj, True)
                #  Update the shared memory map so the watchdog process can stop running.
                self.process_state.value = 1
                return False

            # Fetch the proper function to call
        func = FunctionRouter.get_function(self.destination_target_name, action)

        # Upload the resources. func_dict has the following format:
        #   {
        #        'resources_ignored': resources_ignored,
        #        'resources_updated': resources_updated,
        #        'action_metadata': action_metadata,
        #        'file_metadata_list': file_metadata_list,
        #        'project_id': title
        #    }
        try:
            func_dict = func(self.destination_token, self.destination_resource_id,
                             self.data_directory, self.hash_algorithm, self.file_duplicate_action)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch.
            # Update the server process_info file appropriately.
            self.process_info_obj['status_code'] = e.status_code
            self.process_info_obj['status'] = 'failed'
            if self.action == 'resource_transfer_in':
                self.process_info_obj['upload_status'] = 'failed'
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
        self.upload_fixity = True
        for resource in func_dict['file_metadata_list']:
            resource['failed_fixity_info'] = []
            if resource['destinationHash'] != self.file_hashes[resource['actionRootPath']] \
                    and resource['actionRootPath'] not in func_dict['resources_ignored']:
                self.upload_fixity = False
                self.process_info_obj['failed_fixity'].append(resource['actionRootPath']
                                                              [len(self.data_directory) + 1:])
                resource['failed_fixity_info'].append({
                    'NewGeneratedHash': resource['destinationHash'],
                    'algorithmUsed': self.hash_algorithm,
                    'reasonFixityFailed': "Either the destination did not provide a hash "
                                          "or fixity failed during upload."
                })

        # Strip the server created directory prefix of the file paths for ignored and updated files
        resources_ignored = [file[len(self.data_directory):]
                             for file in func_dict['resources_ignored']]
        self.process_info_obj['resources_ignored'] = resources_ignored
        resources_updated = [file[len(self.data_directory):]
                             for file in func_dict['resources_updated']]
        self.process_info_obj['resources_updated'] = resources_updated

        # If we are transferring the resources then add metadata to the existing fts metadata
        if self.action == 'resource_transfer_in':
            self.metadata_validation = create_upload_transfer_metadata(self,
                                                                       func_dict['file_metadata_list'],
                                                                       func_dict['action_metadata'],
                                                                       func_dict['project_id'],
                                                                       resources_ignored,
                                                                       resources_updated)
            self.process_info_obj['upload_status'] = get_action_message('Upload',
                                                                        self.upload_fixity,
                                                                        self.metadata_validation)
        # Otherwise if we are uploading from a local source then create fts metadata
        # and update the server process file
        else:
            self.metadata_validation = create_upload_metadata(self, func_dict['file_metadata_list'],
                                                              func_dict['action_metadata'],
                                                              func_dict['project_id'],
                                                              resources_ignored, resources_updated)
            # Validate the final metadata
            self.process_info_obj['message'] = get_action_message('Upload',
                                                                  self.upload_fixity,
                                                                  self.metadata_validation)

            # Update server process file
            self.process_info_obj['status_code'] = '200'
            self.process_info_obj['status'] = 'finished'
            self.process_info_obj['hash_algorithm'] = self.hash_algorithm
            write_file(self.process_info_path, self.process_info_obj, True)

            # Update the shared memory map so the watchdog process can stop running.
            self.process_state.value = 1

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
            self.source_target_name, self.source_resource_id = transfer_post_body_validation(
                self.request)
            target_valid, self.infinite_depth = target_validation(
                self.destination_target_name, self.action)
            target_validation(self.source_target_name, 'resource_transfer_out')
            ############# VALIDATION TO ADD #############
            # CHECK THAT source_target_name CAN TRANSFER TO destination_target_name
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Generate ticket number
        ticket_number = uuid4()
        self.ticket_path = os.path.join("mediafiles", "transfers", str(ticket_number))

        # Create directory and process_info json file
        self.process_info_obj = {
            'presqt-source-token': hash_tokens(self.source_token),
            'presqt-destination-token': hash_tokens(self.destination_token),
            'status': 'in_progress',
            'expiration': str(timezone.now() + relativedelta(days=5)),
            'message': 'Transfer is being processed on the server',
            'download_status': None,
            'upload_status': None,
            'status_code': None
        }
        self.process_info_path = os.path.join(self.ticket_path, "process_info.json")
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

        transfer_fixity = False if not self.download_fixity or not self.upload_fixity else True
        self.process_info_obj['message'] = get_action_message(
            'Transfer', transfer_fixity, self.metadata_validation)

        write_file(self.process_info_path, self.process_info_obj, True)

        # Update the shared memory map so the watchdog process can stop running.
        self.process_state.value = 1
        return
