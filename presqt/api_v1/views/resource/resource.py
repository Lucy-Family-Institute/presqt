import multiprocessing
import os
from uuid import uuid4

import bagit
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.reverse import reverse

from presqt.api_v1.serializers.resource import ResourceSerializer
from presqt.api_v1.utilities import (get_source_token, target_validation, FunctionRouter,
                                     spawn_action_process)
from presqt.api_v1.utilities.fixity import download_fixity_checker
from presqt.api_v1.utilities.multiprocess.watchdog import process_watchdog
from presqt.utilities import write_file, read_file, zip_directory
from presqt.api_v1.views.resource.base_resource import BaseResource
from presqt.utilities import PresQTValidationError, PresQTResponseException


class Resource(BaseResource):
    """
    **Supported HTTP Methods**

    * GET:
        - Retrieve a summary of the resource for the given Target that has been requested.
        or
        - Retrieve a Zip file of the resource and prepare the download of it.
    * POST
        - Upload resources to a Target.
        or
        - Transfer resources from one Target to another.
    """
    def get(self, request, target_name, resource_id, resource_format=None):
        """
        Retrieve details about a specific Resource.
        or
        Retrieve a specific Resource in zip format.

        Parameters
        ----------
        request : HTTP Request Object
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
        self.request = request
        self.source_target_name = target_name
        self.source_resource_id = resource_id

        if resource_format == 'json' or resource_format is None:
            self.action = 'resource_detail'
            return self.get_json_format()

        elif resource_format == 'zip':
            self.action = 'resource_download'
            return self.get_zip_format()

        else:
            return Response(
                data={
                    'error': '{} is not a valid format for this endpoint.'.format(resource_format)},
                status=status.HTTP_400_BAD_REQUEST)

    def get_json_format(self):
        """
        Retrieve details about a specific Resource.

        Returns
        -------
        Response object in JSON format
        """
        # Perform token, target, and action validation
        try:
            token = get_source_token(self.request)
            target_validation(self.source_target_name, self.action)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Fetch the proper function to call
        func = FunctionRouter.get_function(self.source_target_name, self.action)

        # Fetch the resource
        try:
            resource = func(token, self.source_resource_id)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch
            return Response(data={'error': e.data}, status=e.status_code)

        serializer = ResourceSerializer(instance=resource, context={
            'target_name': self.source_target_name, 'request': self.request})

        return Response(serializer.data)

    def get_zip_format(self):
        """
        Prepares a download of a resource with the given resource ID provided. Spawns a process
        separate from the request server to do the actual downloading and zip-file preparation.

        Returns
        -------
        Response object with ticket information.
        """
        # Perform token, target, and action validation
        try:
            self.source_token = get_source_token(self.request)
            target_validation(self.source_target_name, self.action)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Generate ticket number
        ticket_number = uuid4()
        self.ticket_path = 'mediafiles/downloads/{}'.format(ticket_number)

        # Create directory and process_info json file
        self.process_info_obj = {
            'presqt-source-token': self.source_token,
            'status': 'in_progress',
            'expiration': str(timezone.now() + relativedelta(days=5)),
            'message': 'Download is being processed on the server',
            'status_code': None
        }

        self.process_info_path = '{}/process_info.json'.format(self.ticket_path)
        write_file(self.process_info_path, self.process_info_obj, True)

        self.base_directory_name = '{}_download_{}'.format(self.source_target_name,
                                                           self.source_resource_id)
        # Spawn the upload_resource method separate from the request server by using multiprocess.
        spawn_action_process(self, self._download_resource)

        # Get the download url
        reversed_url = reverse('download_job', kwargs={'ticket_number': ticket_number})
        download_hyperlink = self.request.build_absolute_uri(reversed_url)

        return Response(status=status.HTTP_202_ACCEPTED,
                        data={'ticket_number': ticket_number,
                              'message': 'The server is processing the request.',
                              'download_job': download_hyperlink})
