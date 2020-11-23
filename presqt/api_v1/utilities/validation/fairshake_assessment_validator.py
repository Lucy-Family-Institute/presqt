from rest_framework import status

from presqt.utilities import PresQTValidationError, read_file


def fairshake_assessment_validator(request, rubric_id):
    """
    """
    try:
        rubric_answers = request.data['rubric_answers']
    except KeyError:
        raise PresQTValidationError(
            "PresQT Error: 'rubric_answers' missing in POST body.",
            status.HTTP_400_BAD_REQUEST
        )

    # Validate that rubric answers is a dict...
    if type(rubric_answers) is not dict:
        raise PresQTValidationError(
            "PresQT Error: 'rubric_answers' must be an object with the metric id's as the keys and answer values as the values.",
            status.HTTP_400_BAD_REQUEST
        )

    test_translator = read_file(
        'presqt/specs/services/fairshake/fairshake_test_fetch.json', True)[rubric_id]
    score_translator = read_file(
        'presqt/specs/services/fairshake/fairshake_score_translator.json', True)

    for key, value in test_translator.items():
        if key not in rubric_answers.keys():
            raise PresQTValidationError(
                f"Missing response for metric '{key}'. Required metrics are: {list(test_translator.keys())}",
                status.HTTP_400_BAD_REQUEST)
    for key, value in rubric_answers.items():
        if value not in score_translator.keys():
            raise PresQTValidationError(
                f"'{value}' is not a valid answer. Options are: {list(score_translator.keys())}",
                status.HTTP_400_BAD_REQUEST)
        if key not in test_translator.keys():
            raise PresQTValidationError(
                f"'{key}' is not a valid metric. Required metrics are: {list(test_translator.keys())}",
                status.HTTP_400_BAD_REQUEST)

    return rubric_answers
