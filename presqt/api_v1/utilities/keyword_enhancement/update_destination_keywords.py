from presqt.api_v1.utilities import FunctionRouter
from presqt.utilities import PresQTResponseException


def update_destination_keywords(self, project_id):
    # Upload enhanced source keywords to destination
    destination_keywords_upload_func = FunctionRouter.get_function(self.destination_target_name, 'keywords_upload')

    try:
        updated_destination_keywords = destination_keywords_upload_func(self.destination_token, project_id, self.all_keywords)
    except PresQTResponseException as e:
        print(e)

    # Upload enhanced source keywords to source
    source_keywords_upload_func = FunctionRouter.get_function(self.source_target_name, 'keywords_upload')

    try:
        updated_source_keywords = source_keywords_upload_func(self.source_token, self.source_resource_id, self.all_keywords)
    except PresQTResponseException as e:
        print(e)