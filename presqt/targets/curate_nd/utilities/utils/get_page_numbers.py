import requests


def get_page_numbers(url, token):
    """
    """
    headers = {"X-Api-Token": token}

    pagination_info = requests.get(url, headers=headers).json()['pagination']

    next_page = None
    previous_page = None
    total_pages = pagination_info['lastPage'].partition('=')[2]
    if total_pages == 'self':
        total_pages = '1'

    if 'previousPage' in pagination_info.keys():
        previous_page = pagination_info['previousPage'].partition('=')[2]
    if 'nextPage' in pagination_info.keys():
        next_page = pagination_info['nextPage'].partition('=')[2]

    pages = {
        "first_page": '1',
        "previous_page": previous_page,
        "next_page": next_page,
        "last_page": total_pages,
        "total_pages": total_pages,
        "per_page": 12
    }
    return pages
