import json

import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.utilities import fairshare_evaluator_validation, fairshare_results
from presqt.utilities import PresQTValidationError


class FairshareEvaluator(APIView):
    def post(self, request):
        """

        Parameters
        ----------
        request

        Returns
        -------
        400: Bad Request
        {
            "error": "PresQT Error: 'resource_id' missing in the request body."
        }
        or
        400: Bad Request
        {
            "error": "PresQT Error: 'executor' missing in the request body."
        }
        or
        400: Bad Request
        {
            "error": "PresQT Error: 'title' missing in the request body."
        }
        """
        try:
            resource_id, executor, title = fairshare_evaluator_validation(request)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        data = {
            'resource': resource_id,
            'executor': executor,
            'title': title
        }

        # TODO: Have the request bring in a collection or set of collection IDS
        # or
        # TODO: or hard code a list of collections
        response = requests.post(
            'https://w3id.org/FAIR_Evaluator/collections/1/evaluate',
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            data=json.dumps(data)
        )

        response_json = response.json()
        results = fairshare_results(response_json)

        return Response(status=status.HTTP_200_OK, data=results)
