import json
import requests


def upload_extra_metadata(extra_metadata, headers, attribute_url):
    """
    Add attributes found in the 'extra_metadata' in PRESQT_FTS_METADATA to the project in Figshare.

    Figshare only supports updating the 'description' attribute.

    Parameters
    ----------
    extra_metadata: dict
        Attributes to add to the project
    headers: dict
        Headers to add to the request
    attribute_url: str
        The url for the request
    """
    if extra_metadata['description']:
        data = json.dumps({'description': extra_metadata['description']})
        requests.put(attribute_url, headers=headers, data=data)
