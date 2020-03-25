import json
from uuid import uuid4

import requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import status

from presqt.api_v1.utilities import get_process_info_data
from presqt.utilities import write_file


class Proposal(APIView):
    """
    Handles shared POST requests to EaaSI api.
    """

    def post(self, request):
        """
        Upload resources to an EaaSI node.

        Parameters
        ----------
        request : HTTP Request Object
        """
        ticket_number = request.data['ticket_number']
        eaasi_token = str(uuid4())
        data = get_process_info_data('downloads', ticket_number)
        data['eaasi_token'] = eaasi_token
        write_file('mediafiles/downloads/{}/process_info.json'.format(ticket_number), data, True)

        eaasi_download_url = reverse('eaasi_download', kwargs={"ticket_number": ticket_number})
        final_eaasi_download_url = '{}?eaasi_token={}'.format(eaasi_download_url, eaasi_token)

        data = {
            "data_url": final_eaasi_download_url,
            "data_type": "bagit+zip"}

        response = requests.post(
            'https://eaasi-portal.emulation.cloud/environment-proposer/api/v1/proposals',
            data=json.dumps(data),
            headers={"Content-Type": "application/json"})

        print(response.json())

        return