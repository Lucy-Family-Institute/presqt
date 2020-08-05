import requests


def get_page_numbers(url, headers, page_number):
    """
    Get the pagination information for the request.

    Parameters
    ----------
    url : str
        The GitHub url
    headers : str
        GitHub authorization headers
    page_number : str
        The page number of the initial request

    Returns
    -------
    A dictionary of page numbers
    """
    try:
        pagination_info = requests.get(url, headers=headers).headers['Link']
    except KeyError:
        return {
            "first_page": '1',
            "previous_page": None,
            "next_page": None,
            "last_page": '1',
            "total_pages": '1',
            "per_page": 30
        }

    previous_page = None
    next_page = None
    last_page = page_number

    # They way they return the pagination info is gross, so this will be equally gross...
    if int(page_number) > 1:
        previous_page = int(page_number) - 1

    if '; rel="last"' in pagination_info:
        last_page = pagination_info.partition('>; rel="last')[0].rpartition('=')[2]

    if '; rel="next"' in pagination_info:
        next_page = pagination_info.partition('>; rel="next')[0].rpartition('=')[2]

    pages = {
        "first_page": '1',
        "previous_page": previous_page,
        "next_page": next_page,
        "last_page": last_page,
        "total_pages": last_page,
        "per_page": 30
    }

    return pages
