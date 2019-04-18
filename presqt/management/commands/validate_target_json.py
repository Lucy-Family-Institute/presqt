from django.core.management import BaseCommand # pragma: no cover


from presqt.json_schemas.schema_handlers import schema_validator # pragma: no cover



class Command(BaseCommand): # pragma: no cover

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