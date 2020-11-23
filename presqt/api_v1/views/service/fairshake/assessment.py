import coreapi
import json
import time

from rest_framework import status, renderers
from rest_framework.response import Response
from rest_framework.views import APIView

from config.settings.base import FAIRSHAKE_TOKEN
from presqt.api_v1.utilities import fairshake_request_validator, fairshake_assessment_validator
from presqt.utilities import PresQTValidationError, read_file


class FairshakeAssessment(APIView):
    """
    """

    renderer_classes = [renderers.JSONRenderer]

    def get(self, request, rubric_id):
        """
        Get details of the provided rubric.
        This includes the metrics expected to be answered by the end user.

        Returns
        -------
        200: OK
        {
            "metrics": {
                "30": "The structure of the repository permits efficient discovery of data and metadata by end users.",
                "31": "The repository uses a standardized protocol to permit access by users.",
                "32": "The repository provides contact information for staff to enable users with questions or suggestions to interact with repository experts.",
                "33": "Tools that can be used to analyze each dataset are listed on the corresponding dataset pages.",
                "34": "The repository maintains licenses to manage data access and use.",
                "35": "The repository hosts data and metadata according to a set of defined criteria to ensure that the resources provided are consistent with the intent of the repository.",
                "36": "The repository provides documentation for each resource to permit its complete and accurate citation.",
                "37": "A description of the methods used to acquire the data is provided.",
                "38": "Version information is provided for each resource, where available."
            },
            "answer_options": {
                "0.0": "no",
                "0.25": "nobut",
                "0.5": "maybe",
                "0.75": "yesbut",
                "1.0": "yes"
            }
        }

        400: Bad Request
        {
            "error": "PresQT Error: 'egg' is not a valid rubric id. Choices are: ['7', '8', '9']"
        }
        """
        rubrics = ['7', '8', '9']
        if rubric_id not in rubrics:
            return Response(data={
                'error': f"PresQT Error: '{rubric_id}' is not a valid rubric id. Choices are: {rubrics}"},
                status=status.HTTP_400_BAD_REQUEST)

        metrics = read_file(
            'presqt/specs/services/fairshake/fairshake_test_fetch.json', True)[rubric_id]
        answer_options = read_file(
            'presqt/specs/services/fairshake/fairshake_score_translator.json', True)
        payload = {
            "metrics": metrics,
            "answer_options": answer_options
        }

        return Response(data=payload, status=status.HTTP_200_OK)

    def post(self, request, rubric_id):
        """
        Returns assessment results to the user.

        Returns
        -------
        200: OK
        {
            "digital_object_id": 166055,
            "rubric_responses": [
                {
                    "metric": "The structure of the repository permits efficient discovery of data and metadata by end users.",
                    "score": "0.0",
                    "score_explanation": "no"
                },
                ...
            ]
        }

        400: Bad Request
        {
            "error": "PresQT Error: 'eggs' is not a valid rubric id. Options are: ['7', '8', '9']"
        }
        or
        {
            "error": "PresQT Error: 'project_url' missing in POST body."
        }
        or
        {
            "error": "PresQT Error: 'project_title' missing in POST body."
        }
        or
        {
            "error": "PresQT Error: 'rubric_answers' missing in POST body."
        }
        or
        {
            "error": "PresQT Error: 'rubric_answers' must be an object with the metric id's as the keys and answer values as the values."
        }
        or
        {
            "error": "Missing response for metric '30'. Required metrics are: ['30', '31', '32']"
        }
        or
        {
            "error": "'egg' is not a valid answer. Options are: ['0.0', '0.25', '0.5', '0.75', '1.0']"
        }
        or
        {
            "error": "'egg' is not a valid metric. Required metrics are: ['30', '31', '32']"
        }
        """
        try:
            rubric_id, digital_object_type, project_url, project_title = fairshake_request_validator(
                request, rubric_id)
            rubric_answers = fairshake_assessment_validator(request, rubric_id)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # First we need to register our new `digital_object` using this information
        # The PresQT project id on FAIRshake is 116
        project_id = 116
        client = coreapi.Client(auth=coreapi.auth.TokenAuthentication(
            token=FAIRSHAKE_TOKEN, scheme='token'))
        schema = client.get('https://fairshake.cloud/coreapi/')

        digital_object = client.action(schema, ['digital_object', 'create'], params=dict(
            url=project_url,
            title=project_title,
            projects=[project_id],
            type=digital_object_type,
            rubrics=[int(rubric_id)]
        ))
        digital_object_id = digital_object['id']

        # Do the assessment here
        assessment_answers = []
        # Need to translate the JSON strings to ints and floats
        for key, value in rubric_answers.items():
            assessment_answers.append({
                'metric': int(key),
                'answer': float(value)
            })

        assessment = client.action(schema, ['assessment', 'create'], params=dict(
            project=project_id,
            target=digital_object_id,
            rubric=int(rubric_id),
            methodology="self",
            answers=assessment_answers))

        # Bring in our translation files...
        test_translator = read_file(
            'presqt/specs/services/fairshake/fairshake_test_fetch.json', True)[rubric_id]
        score_translator = read_file(
            'presqt/specs/services/fairshake/fairshake_score_translator.json', True)

        results = []
        for score in assessment['answers']:
            metric = test_translator[str(score['metric'])]
            score_number = str(score['answer'])
            score_words = 'not applicable'
            # Adding the != because 0.0 also returns False
            if value != None:
                score_words = score_translator[score_number]
            results.append({
                "metric": metric,
                "score": score_number,
                "score_explanation": score_words
            })

        payload = {
            "digital_object_id": digital_object_id,
            "rubric_responses": results
        }

        return Response(status=status.HTTP_200_OK,
                        data=payload)