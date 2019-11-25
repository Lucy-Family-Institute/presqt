import json

from jsonschema import validate, ValidationError
from presqt.utilities import PresQTError


def schema_validator(json_schema_path, json_data):
    """
    Uses JSONSchema validator to validate JSON file against JSONSchema provided.

    Parameters
    ----------
    json_file_path : str
        Path of the JSON file we are validating

    json_data : str or dict
        Path of the JSON file we are validating against or the python dict to validate against

    Returns
    -------
        True if the validation passes
        ValidationError object if the validation fails
    """
    with open(json_schema_path) as json_schema_file:
        json_schema = json.load(json_schema_file)

    if isinstance(json_data, str):
        try:
            with open(json_data) as json_file:
                json_data = json.load(json_file)
            validate(instance=json_data, schema=json_schema)
        except (ValidationError, FileNotFoundError) as e:
            return e
        else:
            return True

    elif isinstance(json_data, dict):
        try:
            validate(instance=json_data, schema=json_schema)
        except ValidationError as e:
            return e
        else:
            return True
