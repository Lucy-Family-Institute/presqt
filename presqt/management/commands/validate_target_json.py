from django.core.management import BaseCommand

from presqt.api_v1.utilities.utils.function_router import FunctionRouter
from presqt.utilities import read_file
from presqt.json_schemas.schema_handlers import schema_validator


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Verify that the Target JSON file is valid against our JSON Schema
        """
        keys_to_validate = ['resource_collection']

        validation = schema_validator(
            'presqt/json_schemas/target_schema.json',
            'presqt/targets.json')

        failure_string = "Target JSON Schema Validation Failed!\n" \
                         "You've modified the targets.json in such a way that it is incorrectly " \
                         "formatted.\nPlease refer to the project docs."

        # If JSON Schema validation has failed
        if validation is not True:
            print(validation)
            print(failure_string)
            exit(0)
        else:
            # Further validation
            json_data = read_file('presqt/targets.json', True)

            name_list = []
            for data in json_data:
                # Verify that there are no duplicate name values
                if data['name'] in name_list:
                    print(failure_string)
                    exit(1)
                    break
                # Verify that all actions for this target which are 'true' have a corresponding
                # function in FunctionRouter for it.
                for key, value in data.items():
                    if key in keys_to_validate and value is True:
                        try:
                            getattr(FunctionRouter, '{}_{}'.format(data['name'], key))
                        except AttributeError:
                            print('{} does not have a corresponding function in FunctionRouter for '
                                  'the attribute {}'.format(data['name'], key))
                            exit(2)
                else:
                    name_list.append(data['name'])

            # Validation has passed!
            print("Target JSON Schema Validation Passed")
