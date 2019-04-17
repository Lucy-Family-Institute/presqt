from django.core.management import BaseCommand

from presqt.json_schemas.schema_handlers import schema_validator


class Command(BaseCommand):
    def handle(self, *args, **options):
        validation = schema_validator(
            'presqt/targets.json',
            'presqt/json_schemas/target_schema.json'
        )


        if validation is not True:
            print(validation)
            print("Target JSON Schema Validation Failed!")
            exit(1)
        else:
            print("Target JSON Schema Validation Passed")