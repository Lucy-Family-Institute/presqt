

def extra_metadata_helper(resource_obj):
    """
    Build extra metadata dict to help with other integrations.

    Parameters
    ----------
    resource_obj: dict
        The resource we are pulling metadata from

    Returns
    -------
        Extra metadata dictionary
    """
    # Get creator name
    if 'creator#author' in resource_obj.extra.keys():
        name_helper = resource_obj.extra['creator#author'].partition(' ')
    else:
        name_helper = resource_obj.extra['creator'].partition(' ')
    first_name = name_helper[0]
    last_name = name_helper[2]

    description = None
    if 'description#abstract' in resource_obj.extra.keys():
        description = resource_obj.extra['description#abstract']

    extra_metadata = {
        "title": resource_obj.title,
        "creators": [
            {
                "first_name": first_name,
                "last_name": last_name,
                "ORCID": None
            }
        ],
        "publication_date": resource_obj.date_submitted,
        "description": description,
        "keywords": [],
        "license": resource_obj.extra['rights'],
        "related_identifiers": [],
        "references": None,
        "notes": None
    }

    return extra_metadata
