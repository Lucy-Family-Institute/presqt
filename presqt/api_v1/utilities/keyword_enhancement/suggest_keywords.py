from presqt.api_v1.utilities import FunctionRouter, keyword_enhancer
from presqt.utilities import PresQTResponseException


def suggest_keywords(self):
    # Fetch the source keywords
    keyword_fetch_func = FunctionRouter.get_function(self.source_target_name, 'keywords')
    try:
        source_keywords = keyword_fetch_func(self.source_token, self.source_resource_id)['keywords']
    except PresQTResponseException:
        return {}

    self.all_keywords = source_keywords + self.all_keywords

    # Enhance source keywords
    try:
        self.suggested_keywords, all_keywords = keyword_enhancer(self.all_keywords)
    except PresQTResponseException:
        self.initial_keywords = []
        self.enhanced_keywords = []

    keyword_dict = {}

    return keyword_dict