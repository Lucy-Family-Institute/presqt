import json

from jsonschema import validate, ValidationError


def schema_validator(json_file_path, json_schema_path):
    with open(json_file_path) as json_file:
        json_data = json.load(json_file)

    with open(json_schema_path) as json_schema_file:
        json_schema = json.load(json_schema_file)

    try:
        validate(instance=json_data, schema=json_schema)
    except ValidationError as e:
        return e
    else:
        return True