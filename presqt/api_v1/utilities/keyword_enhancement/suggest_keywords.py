from presqt.api_v1.utilities import FunctionRouter, keyword_enhancer
from presqt.utilities import PresQTResponseException


def suggest_keywords(self):
    """
    Get a list of suggested enhanced keywords based on the source target's keywords and keywords
    found in the source's FTS metadata file (if one exists).
    Save the suggested keywords to self.suggested_keywords.
    Save the source's keywords to self.all_keywords.
    """
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