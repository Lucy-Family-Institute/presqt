import json

from django.core.management import BaseCommand


from presqt.json_schemas.schema_handlers import schema_validator



class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Verify that the Target JSON file is valid against our JSON Schema
        """
        validation = schema_validator(
            'presqt/targets.json',
            'presqt/json_schemas/target_schema.json'
        )

        # If JSON Schema validation has failed
        if validation is not True:
            print(validation)
            print("Target JSON Schema Validation Failed!")
            exit(1)
        else:
            # Verify that there are no duplicate name values
            with open('presqt/targets.json') as json_file:
                json_data = json.load(json_file)

            name_list = []
            for data in json_data:
                if data['name'] in name_list:
                    print("There are duplicate objects with the 'name': {}".format(data['name']))
                    print("You've modified the targets.json in such a way that it is incorrectly formatted.\n"
                          "Please refer to the project documentation.")
                    print("Target JSON Schema Validation Failed!")
                    exit(1)
                    break
                else:
                    name_list.append(data['name'])

            # Validation has passed!
            print("Target JSON Schema Validation Passed")
