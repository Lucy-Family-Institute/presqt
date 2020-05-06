from presqt.api_v1.utilities import FunctionRouter, keyword_enhancer
from presqt.utilities import PresQTResponseException


def enhance_keywords(self):
    # Fetch the source keywords
    keyword_fetch_func = FunctionRouter.get_function(self.source_target_name, 'keywords')
    try:
        source_keywords = keyword_fetch_func(self.source_token, self.source_resource_id)['keywords']
    except PresQTResponseException as e:
        # If the keyword fails then return that error
        metadata_validation = e

    self.source_keywords = source_keywords + self.source_keywords

    # Enhance source keywords
    self.enhanced_keywords, self.all_keywords = keyword_enhancer(self.source_keywords)

    keyword_dict = {
        'initialKeywords': self.source_keywords,
        'enhancedKeywords': self.enhanced_keywords,
        'enhancer': 'scigraph'
    }

    return keyword_dict