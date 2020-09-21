import requests


def get_page_numbers(url, headers):
    """
    Get the pagination information for the request.

    Parameters
    ----------
    url : str
        The GitLab url
    headers : str
        GitLab authorization headers

    Returns
    -------
    A dictionary of page numbers
    """
    page_info = requests.get(url, headers=headers).headers

    if not page_info['X-Prev-Page']:
        page_info['X-Prev-Page'] = None
    if not page_info['X-Next-Page']:
        page_info['X-Next-Page'] = None

    pages = {
        "first_page": '1',
        "previous_page": page_info['X-Prev-Page'],
        "next_page": page_info['X-Next-Page'],
        "last_page": page_info['X-Total-Pages'],
        "total_pages": page_info['X-Total-Pages'],
        "per_page": page_info['X-Per-Page']
    }

    return pages
