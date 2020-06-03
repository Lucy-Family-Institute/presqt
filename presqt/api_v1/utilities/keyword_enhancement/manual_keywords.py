from presqt.api_v1.utilities import FunctionRouter
from presqt.utilities import PresQTResponseException


def manual_keywords(self):
    """
    Get a list of source keywords to add to the destination project.
    Save the source's keywords to self.all_keywords.
    """
    # Fetch the source keywords
    keyword_fetch_func = FunctionRouter.get_function(self.source_target_name, 'keywords')
    try:
        source_keywords = keyword_fetch_func(self.source_token, self.source_resource_id)['keywords']
        self.initial_keywords = source_keywords
    except PresQTResponseException:
        return {}

    self.all_keywords = list(set(source_keywords + self.all_keywords + self.keywords))

    return {
        'sourceKeywordsAdded': self.initial_keywords,
        'sourceKeywordsEnhanced': self.keywords,
        'enhancer': 'scigraph'
    }
