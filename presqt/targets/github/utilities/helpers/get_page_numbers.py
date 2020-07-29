import requests


def get_page_numbers(url, headers, page_number):
    """
    """
    pagination_info = requests.get(url, headers=headers).headers['Link']
    # They way they return this is gross, so this will be equally gross...
    previous_page = None
    next_page = None
    last_page = page_number

    if int(page_number) > 1:
        previous_page = int(page_number) - 1

    if '; rel="last"' in pagination_info:
        last_page = pagination_info.rpartition(', ')[2].rpartition('>')[0].rpartition('=')[2]

    if '; rel="next"' in pagination_info:
        next_page = pagination_info.partition('>')[0].rpartition('=')[2]

    pages = {
        "first_page": '1',
        "previous_page": previous_page,
        "next_page": next_page,
        "last_page": last_page,
        "total_pages": last_page,
        "per_page": 30
    }

    return pages
