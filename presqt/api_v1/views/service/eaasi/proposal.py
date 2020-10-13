import json
from uuid import uuid4

import requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import status, renderers

from presqt.api_v1.utilities import (get_process_info_data, get_source_token, hash_tokens,
                                     get_process_info_action)
from presqt.utilities import write_file, PresQTValidationError


class Proposals(APIView):
    """
    **Supported HTTP Methods**

    * POST:
        - Send an EaaSI download URL to the EaaSI API to start a proposal task.
    """

    renderer_classes = [renderers.JSONRenderer]

    def post(self, request):
        """
        Upload a proposal task to EaaSI

        Returns
        -------
        200: OK
        {
            "id": "19",
            "message": "Proposal task was submitted."
            "proposal_link": "https://localhost/api_v1/services/eaasi/1/"
        }

        400: Bad Request
        {
            "error": "PresQT Error: 'presqt-source-token' missing in the request headers."
        }
        or
        {
            "error": "PresQT Error: A download does not exist for this user on the server."
        }

        404: Not Found
        {
            "error": "PresQT Error: Invalid ticket number, '1234'."
        }
        or
        {
            "error": "PresQT Error: A resource_download does not exist for this user on the server."
        }
        """
        # Get the source token from the request, hash it to get the ticket_number, get the
        # process_info.json file connected with the ticket_number.
        try:
            source_token = get_source_token(self.request)
            ticket_number = hash_tokens(source_token)
            process_info_data = get_process_info_data(ticket_number)
            download_data = get_process_info_action(process_info_data, 'resource_download')
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Create a one time use token for EaaSI to use.
        eaasi_token = str(uuid4())
        download_data['eaasi_token'] = eaasi_token
        write_file('mediafiles/jobs/{}/process_info.json'.format(ticket_number), process_info_data, True)

        # Build EaaSI download endpoint url
        eaasi_download_reverse = reverse('eaasi_download', kwargs={"ticket_number": ticket_number})
        eaasi_download_url = request.build_absolute_uri(eaasi_download_reverse)
        final_eaasi_download_url = '{}?eaasi_token={}'.format(eaasi_download_url, eaasi_token)

        data = {
            "data_url": final_eaasi_download_url,
            "data_type": "bagit+zip"
        }

        response = requests.post(
            'https://eaasi-portal.emulation.cloud/environment-proposer/api/v1/proposals',
            data=json.dumps(data),
            headers={"Content-Type": "application/json"})

        if response.status_code != 202:
            return Response(
                data={'message': 'Proposal submission returned a status code of {}.'.format(
                    response.status_code)},
                status=response.status_code)

        response_json = response.json()

        # Add Proposal link to payload
        reverse_proposal_url = reverse('proposal', kwargs={"proposal_id": response_json['id']})
        response_json['proposal_link'] = request.build_absolute_uri(reverse_proposal_url)

        return Response(data=response_json, status=status.HTTP_200_OK)


class Proposal(APIView):
    """
    **Supported HTTP Methods**

    * GET:
        - Poll a proposal task
    """

    renderer_classes = [renderers.JSONRenderer]

    def get(self, request, proposal_id):
        """
        200: OK
        {
            "image_url": "https://eaasi-portal.emulation.cloud:443/blobstore/api/v1/blobs/imagebuilder-outputs/2ca330d6-23f7-4f0a-943a-e3984b29642c?access_token=default",
            "image_type": "cdrom",
            "environments": [],
            "suggested": {}
        }

        202 : Accepted
        {
            "message": "Proposal task is still in progress."
        }

        404
        {
            "message": "Passed ID is invalid: 17"
        }
        """
        wait_queue_url = 'https://eaasi-portal.emulation.cloud/environment-proposer/api/v1/waitqueue/{}'.format(proposal_id)
        response = requests.get(wait_queue_url)
        try:
            response.headers['Location']
            return Response(
                data={"message": "Proposal task is still in progress."},
                status=status.HTTP_202_ACCEPTED)
        except KeyError:
            return Response(data=response.json(), status=response.status_code)
