from rest_framework.reverse import reverse


def page_links(self, target_name, search_params, pages):
    """
    Build links for pagination purposes.

    Parameters
    ----------
    target_name : str
        The string name of the Target resource to retrieve.
    pages : dict
        A dictionary of page information from the target.
    search_params : dict
        The search parameters requested by the user.

    Returns
    -------
    A new dictionary with linked pages.
    """
    reversed_url = reverse('resource_collection', kwargs={'target_name': target_name})
    base_url = self.request.build_absolute_uri(reversed_url).rpartition('/')[0]

    # Set previous and next page variables pulling from passed in pages dict
    previous_page = pages['previous_page']
    next_page = pages['next_page']

    if search_params:
        search_key = list(search_params.keys())[0]
        search_value = list(search_params.values())[0]

        # Check for no values
        if previous_page:
            previous_page = "{}?{}={}&page={}".format(base_url, search_key, search_value, previous_page)
        if next_page:
            next_page = "{}?{}={}&page={}".format(base_url, search_key, search_value, next_page)

        first_page = "{}?{}={}&page={}".format(base_url, search_key, search_value, pages['first_page'])
        last_page = "{}?{}={}&page={}".format(base_url, search_key, search_value, pages['last_page'])

    else:
        # Check for no values
        if previous_page:
            previous_page = "{}?page={}".format(base_url, previous_page)
        if next_page:
            next_page = "{}?page={}".format(base_url, next_page)

        first_page = "{}?page={}".format(base_url, pages['first_page'])
        last_page = "{}?page={}".format(base_url, pages['last_page'])

    linked_pages = {
        "first_page": first_page,
        "previous_page": previous_page,
        "next_page": next_page,
        "last_page": last_page,
        "total_pages": pages['total_pages'],
        "per_page": pages['per_page']
    }

    return linked_pages
