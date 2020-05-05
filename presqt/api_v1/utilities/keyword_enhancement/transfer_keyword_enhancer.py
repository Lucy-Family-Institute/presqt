from presqt.api_v1.utilities import FunctionRouter
from presqt.utilities import PresQTResponseException


def transfer_keyword_enhancer(self):
    # Fetch the source keywords
    keyword_fetch_func = FunctionRouter.get_function(self.source_target_name, 'keywords')
    try:
        source_keywords = keyword_fetch_func(self.source_token, self.source_resource_id)['keywords']
    except PresQTResponseException as e:
        # If the keyword fails then return that error
        metadata_validation = e
    print(source_keywords)
    print(self.source_main_keywords)
    # Add keywords to file

    # Add keywords to destination resource
    # Write file to destination

    # Add keywords to source resource
    # Write file to source

    return