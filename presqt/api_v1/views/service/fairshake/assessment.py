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

        400: Bad Request
        "PresQT Error: '{rubric_id}'
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

        400: Bad Request
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
        print(digital_object)
        digital_object_id = digital_object['id']

        # Do the assessment here
        assessment_answers = []
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
        print(json.dumps(assessment))
        # Bring in our translation files...
        test_translator = read_file(
            'presqt/specs/services/fairshake/fairshake_test_fetch.json', True)
        score_translator = read_file(
            'presqt/specs/services/fairshake/fairshake_score_translator.json', True)

        results = []
        # for key, value in score['scores'][rubric_id].items():
        #     metric = test_translator[rubric_id][key]
        #     score_number = value
        #     score_words = 'not applicable'
        #     # Adding the != because 0.0 also returns False
        #     if value != None:
        #         score_words = score_translator[str(value)]
        #     results.append({
        #         "metric": metric,
        #         "score": score_number,
        #         "score_explanation": score_words
        #     })

        # Delete the newly created digital object -- This can be discussed with PIs
        # client.action(schema, ['digital_object', 'remove'], params=dict(
        #     id=digital_object_id
        # ))
        return Response(status=status.HTTP_200_OK,
                        data=results)
