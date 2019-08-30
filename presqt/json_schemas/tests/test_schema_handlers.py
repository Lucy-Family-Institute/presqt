import json
import os

from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from presqt.json_schemas.schema_handlers import schema_validator


class TestSchemaValidator(SimpleTestCase):
    """
    Test the function `schema_validator()`
    """
    def setUp(self):
        self.target_json_path = 'presqt/targets.json'
        self.schema_path = 'presqt/json_schemas/target_schema.json'

    def test_valid_json(self):
        """
        Return True if valid JSON file and JSONSchema are provided
        """
        validation = schema_validator(self.target_json_path, self.schema_path)
        self.assertEqual(validation, True)

    def test_invalid_json(self):
        """
        Return ValidationError if invalid JSON file and JSONSchema are provided
        """
        invalid_json = [{'name': 3}]
        invalid_path = 'presqt/json_schemas/tests/test_json_file.json'

        # Create the test JSON file
        with open(invalid_path, 'w') as json_file:
            json.dump(invalid_json, json_file)

        schema_validator(invalid_path, self.schema_path)
        # Verify that the schema_validator returns a ValidationError
        self.assertRaises(ValidationError)

        # Delete the test JSON file
        os.remove(invalid_path)