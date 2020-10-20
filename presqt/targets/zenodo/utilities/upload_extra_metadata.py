import json
import requests


def upload_extra_metadata(extra_metadata, auth_parameter, attribute_url):
    """
    Add attributes found in the 'extra_metadata' in PRESQT_FTS_METADATA to the project in OSf.

    OSF only supports updating the 'description' attribute.

    Parameters
    ----------
    extra_metadata: dict
        Attributes to add to the project
    auth_parameter: dict
        Authentication parameters
    attribute_url: str
        The url for the request
    """
    data = {
            "metadata": {
                "upload_type": "other",
                "title": extra_metadata['title']
            }
        }

    if extra_metadata['description']:
        data["metadata"]['description'] = extra_metadata['description']

    if extra_metadata['creators']:
        data["metadata"]['creators'] = []
        for creator in extra_metadata['creators']:
            creator_dict = {
                    "name": '{} {}'.format(creator['first_name'], creator['last_name']),
                    "affiliation": "",
                }

            if creator["ORCID"]:
                creator_dict['orcid'] = creator["ORCID"]

            data["metadata"]['creators'].append(creator_dict)

    if extra_metadata['license']:
        data["metadata"]["license"] = "MIT"

    if extra_metadata['publication_date']:
        data["metadata"]["publication_date"] = extra_metadata['publication_date']

    if extra_metadata['related_identifiers']:
        data["metadata"]["related_identifiers"] = [
            {
                'relation': 'isIdenticalTo',
                'identifier': identifier['identifier']
            }
            for identifier in extra_metadata['related_identifiers']
        ]

    if extra_metadata['references']:
        data["metadata"]["references"] = extra_metadata['references']

    if extra_metadata['notes']:
        data["metadata"]["notes"] = extra_metadata['notes']

    requests.put(attribute_url,
                 params=auth_parameter,
                 data=json.dumps(data),
                 headers={"Content-Type": "application/json"})