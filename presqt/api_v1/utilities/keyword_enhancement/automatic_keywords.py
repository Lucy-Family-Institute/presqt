from presqt.api_v1.utilities import FunctionRouter, keyword_enhancer
from presqt.utilities import PresQTResponseException


def automatic_keywords(self):
    """
    Enhance keywords found at the source target and in the source target's FTS metadata file.
    Save the list of enhanced keywords to self.enhanced_keywords.
    Save the full list of keywords (source keywords and enhanced keywords) to self.all_keywords.
    Save the source's initial keywords to self.initial_keywords.
    """
    # Fetch the source keywords
    keyword_fetch_func = FunctionRouter.get_function(self.source_target_name, 'keywords')
    try:
        source_keywords = keyword_fetch_func(self.source_token, self.source_resource_id)['keywords']
    except PresQTResponseException:
        return {}

    self.all_keywords = list(set(source_keywords + self.all_keywords))
    self.initial_keywords = self.all_keywords

    # Enhance source keywords
    try:
        self.enhanced_keywords, self.all_keywords = keyword_enhancer(self.all_keywords)
    except PresQTResponseException:
        self.initial_keywords = []
        self.enhanced_keywords = []
    
    self.all_keywords = self.all_keywords + self.keywords

    keyword_dict = {
        'sourceKeywordsAdded': self.initial_keywords,
        'sourceKeywordsEnhanced': list(set(self.enhanced_keywords + self.keywords)),
        'enhancer': 'scigraph'
    }

    return keyword_dict
