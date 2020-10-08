import json

import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.utilities import (
    fairshare_results, fairshare_request_validator, fairshare_test_validator, get_user_email_opt)
from presqt.api_v1.utilities.utils.send_email import email_blaster
from presqt.utilities import PresQTValidationError, read_file


class FairshareEvaluator(APIView):
    """
    """

    def get(self, request):
        """
        Returns the list of tests available to the user.

        Returns
        -------
        200: OK
        [
            {
                "test_name": "FAIR Metrics Gen2- Unique Identifier "
                "description": "Metric to test if the metadata resource has a unique identifier. This is done by comparing the GUID to the patterns (by regexp) of known GUID schemas such as URLs and DOIs. Known schema are registered in FAIRSharing (https://fairsharing.org/standards/?q=&selected_facets=type_exact:identifier%20schema)",
                "test_id": 1
            },
            {
                "test_name": "FAIR Metrics Gen2 - Identifier Persistence "
                "description": "Metric to test if the unique identifier of the metadata resource is likely to be persistent. Known schema are registered in FAIRSharing (https://fairsharing.org/standards/?q=&selected_facets=type_exact:identifier%20schema). For URLs that don't follow a schema in FAIRSharing we test known URL persistence schemas (purl, oclc, fdlp, purlz, w3id, ark).",
                "test_id": 2
            }...
        ]
        """
        fairshare_test_info = read_file("presqt/specs/services/fairshare/fairshare_description_fetch.json",
                                        True)
        test_list = [
            {"test_name": value['test_name'],
             "description": value['description'],
             "test_id": int(key.rpartition("/")[2])
             } for key, value in fairshare_test_info.items()]

        return Response(status=status.HTTP_200_OK, data=test_list)

    def post(self, request):
        """
        Send an evaluation request to FAIRshare.

        Returns
        -------
        200: OK
        [
            {
                "metric_link": "https://w3id.org/FAIR_Evaluator/metrics/1",
                "test_name": "FAIR Metrics Gen2- Unique Identifier ",
                "description": "Metric to test if the metadata resource has a unique identifier. This is done by comparing the GUID to the patterns (by regexp) of known GUID schemas such as URLs and DOIs. Known schema are registered in FAIRSharing (https://fairsharing.org/standards/?q=&selected_facets=type_exact:identifier%20schema)",
                "successes": [
                    "Found an identifier of type 'doi'"
                ],
                "failures": [],
                "warnings": []
            },
            {
                "metric_link": "https://w3id.org/FAIR_Evaluator/metrics/2",
                "test_name": "FAIR Metrics Gen2 - Identifier Persistence ",
                "description": "Metric to test if the unique identifier of the metadata resource is likely to be persistent. Known schema are registered in FAIRSharing (https://fairsharing.org/standards/?q=&selected_facets=type_exact:identifier%20schema). For URLs that don't follow a schema in FAIRSharing we test known URL persistence schemas (purl, oclc, fdlp, purlz, w3id, ark).",
                "successes": [
                    "The GUID of the metadata is a doi, which is known to be persistent."
                ],
                "failures": [],
                "warnings": []
            }...
        ]
        or
        400: Bad Request
        {
            "error": "PresQT Error: 'resource_id' missing in the request body."
        }
        or
        400: Bad Request
        {
            "error": "PresQT Error: 'tests' missing in the request body."
        }
        or
        400: Bad Request
        {
            "error": "PresQT Error: 'tests' must be in list format."
        }
        or
        400: Bad Request
        {
            "error": "PresQT Error: At least one test is required. Options are: [.......]"
        }
        or
        400: Bad Request
        {
            "error": "PresQT Error: 'eggs' not a valid test name. Options are: [.......]"
        }
        or
        503: Service Unavailable
        {
            "error": "FAIRshare returned a <status_code> error trying to process the request"
        }


        """
        try:
            resource_id, tests = fairshare_request_validator(request)
            email = get_user_email_opt(request)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)
        fairshare_test_info = read_file("presqt/specs/services/fairshare/fairshare_description_fetch.json",
                                        True)
        try:
            test_list = fairshare_test_validator(tests, fairshare_test_info)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        data = {
            'resource': resource_id,
            'executor': "PresQT",
            'title': "PresQT Fair Evaluation"
        }

        # 16 is the id of the PresQT test collection
        response = requests.post(
            'https://w3id.org/FAIR_Evaluator/collections/16/evaluate',
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            data=json.dumps(data))

        if response.status_code != 200:
            return Response(data={'error': "FAIRshare returned a {} error trying to process the request".format(response.status_code)},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        response_json = response.json()
        results = fairshare_results(response_json, test_list)

        if email:
            message = "The FAIRshare Evaluator process you started on PresQT for doi '{}' has finished.\n\n ----EVALUATION RESULTS----\n".format(resource_id)
            details = "{}{}".format(message, json.dumps(results, indent=4))
            # Send the email
            email_blaster(email, "PresQT FAIRshare Evaluator Results", details)

        return Response(status=status.HTTP_200_OK, data=results)
