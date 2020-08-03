import requests


def get_page_numbers(url, token):
    """
    Get the pagination information for the request.

    Parameters
    ----------
    url : str
        The CurateND url
    token : str
        The CurateND token

    Returns
    -------
    A dictionary of page numbers
    """
    headers = {"X-Api-Token": token}

    pagination_info = requests.get(url, headers=headers).json()['pagination']

    next_page = None
    previous_page = None
    total_pages = pagination_info['lastPage'].partition('page=')[2].partition('&')[0]

    # If there is only 1 page of results, instead of a number Curate returns 'self'
    if total_pages == 'self':
        total_pages = '1'

    # We are using partitions to pull the page numbers out of the links that Curate is returning
    if 'previousPage' in pagination_info.keys():
        previous_page = pagination_info['previousPage'].partition('page=')[2].partition('&')[0]
    if 'nextPage' in pagination_info.keys():
        next_page = pagination_info['nextPage'].partition('page=')[2].partition('&')[0]

    pages = {
        "first_page": '1',
        "previous_page": previous_page,
        "next_page": next_page,
        "last_page": total_pages,
        "total_pages": total_pages,
        "per_page": 12
    }

    return pages
