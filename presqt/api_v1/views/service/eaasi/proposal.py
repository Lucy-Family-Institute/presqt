import json
from uuid import uuid4

import requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import status

from presqt.api_v1.utilities import get_process_info_data
from presqt.utilities import write_file


class Proposals(APIView):
    """
    Handles shared POST requests to EaaSI api.
    """

    def post(self, request):
        """
        Upload resources to an EaaSI node.

        Parameters
        ----------
        request : HTTP Request Object

        200
        400
        """
        try:
            ticket_number = request.data['ticket_number']
        except KeyError:
            return Response(data={"error": "ticket_number is missing from the request body."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Create a one time use token for EaaSI to use.
        eaasi_token = str(uuid4())
        data = get_process_info_data('downloads', ticket_number)
        data['eaasi_token'] = eaasi_token
        write_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number), data, True)

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

        return Response(data=response.json(), status=status.HTTP_200_OK)

class Proposal(APIView):
    """

    """
    def get(self, request, proposal_id):
        """
        202
        404
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
