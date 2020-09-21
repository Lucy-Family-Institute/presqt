import requests


def fetch_ontologies(enhanced_keywords):
    """
    Fetch the connected ontology for each enhanced keyword.

    Parameters
    ----------
    enhanced_keywords: list
        List of enhanced keywords in string format

    Returns
    -------
    A list of dictionaries. Each one containing the ontology information for an enhanced keyword
    """

    ontologies = []

    for keyword in enhanced_keywords:
        response = requests.get(
            'http://ec-scigraph.sdsc.edu:9000/scigraph/vocabulary/term/{}?limit=20'.format(keyword))

        if response.status_code == 200:
            for entry in ontologies:
                if response.json()[0]["uri"] == entry['ontology']:
                    entry['keywords'].append(keyword)
                    break
            else:
                ontologies.append({
                    "keywords": [keyword],
                    "ontology": response.json()[0]["uri"],
                    "ontology_id": response.json()[0]["fragment"],
                    "categories": response.json()[0]['categories'],
                })

    return ontologies