from rest_framework.reverse import reverse


def page_links(self, target_name, pages):
    """
    Build links for pagination purposes.

    Parameters
    ----------
    target_name : str
        The string name of the Target resource to retrieve.
    pages : dict
        A dictionary of page information from the target.
    
    Returns
    -------
    A new dictionary with linked pages.
    """
    reversed_url = reverse('resource_collection', kwargs={'target_name': target_name})
    base_url = self.request.build_absolute_uri(reversed_url).rpartition('/')[0]

    # Check for no values
    if pages['previous_page']:
        pages['previous_page'] = "{}{}".format(base_url, "?page={}".format(pages['previous_page']))
    if pages['next_page']:
        pages['next_page'] = "{}{}".format(base_url, "?page={}".format(pages['next_page']))

    linked_pages = {
        "first_page": "{}{}".format(base_url, "?page={}".format(pages['first_page'])),
        "previous_page": pages['previous_page'],
        "next_page": pages['next_page'],
        "last_page": "{}{}".format(base_url, "?page={}".format(pages['last_page'])),
        "total_pages": pages['total_pages'],
        "per_page": pages['per_page']
    }

    return linked_pages
