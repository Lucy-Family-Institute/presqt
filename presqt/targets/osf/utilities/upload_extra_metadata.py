import json
import requests


def upload_extra_metadata(extra_metadata, headers, attribute_url, project_id):
    """
    Add attributes found in the 'extra_metadata' in PRESQT_FTS_METADATA to the project in OSf.

    OSF only supports updating the 'description' attribute.

    Parameters
    ----------
    extra_metadata: dict
        Attributes to add to the project
    headers: dict
        Headers to add to the request
    attribute_url: str
        The url for the request
    project_id: str
        Project ID of the project being updated
    """
    if extra_metadata['description']:
        data = json.dumps({
            "data": {
                "type": "nodes",
                "id": project_id,
                "attributes": {
                    "description": extra_metadata['description']
                }
              }
         })

        headers['Content-Type'] = 'application/json'
        requests.patch(attribute_url, headers=headers, data=data)