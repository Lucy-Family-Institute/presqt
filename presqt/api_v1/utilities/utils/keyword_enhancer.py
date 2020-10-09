import requests
from rest_framework import status
from presqt.utilities import PresQTResponseException


def keyword_enhancer(keywords):
    """
    Send a list of keywords to SciGraph to be enhanced.

    Parameters
    ----------
    keywords: list
        The list of keywords to be enhanced.

    Returns
    -------
    The enhanced list of keywords.
    """
    if not keywords:
        raise PresQTResponseException('There are no keywords to enhance for this resource.',
                                      status.HTTP_400_BAD_REQUEST)

    new_list_of_keywords = []
    final_list_of_keywords = []
    keyword_lower_case = [keyword.lower() for keyword in keywords]
    # Get the new keyword suggestions from Sci-Graph
    for keyword in keyword_lower_case:
        final_list_of_keywords.append(keyword)
        # Get SciGraph 'term' keyword suggestions
        response = requests.get(
            'http://ec-scigraph.sdsc.edu:9000/scigraph/vocabulary/term/{}?limit=20'.format(keyword))
        if response.status_code == 200:
            for label in response.json()[0]['labels']:
                label_lower_case = label.lower()
                if label_lower_case not in keyword_lower_case:
                    new_list_of_keywords.append(label_lower_case)
                    final_list_of_keywords.append(label_lower_case)
    return list(set(new_list_of_keywords)), list(set(final_list_of_keywords))
