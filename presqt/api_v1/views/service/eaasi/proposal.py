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

        download_job_url = reverse('download_job', kwargs={"ticket_number": ticket_number})
        final_download_job_url = '{}?eaasi_token={}'.format(download_job_url, eaasi_token)

        # data = {
        #     "data_url": "https://presqt.readthedocs.io/en/latest/_downloads/cca126b15be422e27bfe28e0b7f994db/NewProjectWithFolderBagIt.zip",
        #     "data_type": "bagit+zip"}

        # response = requests.post(
        #     'https://eaasi-portal.emulation.cloud/environment-proposer/api/v1/proposals',
        #     data=json.dumps(data),
        #     headers={"Content-Type": "application/json"})

        return Response(data={}, status=status.HTTP_202_ACCEPTED)
