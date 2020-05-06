from presqt.api_v1.utilities import FunctionRouter
from presqt.utilities import PresQTResponseException


def update_destination_keywords(self, project_id):
    keywords_upload_func = FunctionRouter.get_function(self.destination_target_name, 'keywords_upload')

    try:
        updated_keywords = keywords_upload_func(self.destination_token, project_id, self.all_keywords)
        print(updated_keywords)
    except PresQTResponseException as e:
        print(e)
    else:
        return updated_keywords
