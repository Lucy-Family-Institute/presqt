import math


def get_page_numbers(resources, page):
    """
    Get the pagination information for the request.

    Parameters
    ----------
    resources: array
        List of top level resources
    page: int
        Page number passed through the query parameters

    Returns
    -------
    A dictionary of page numbers
    """

    total_page = 1
    if len(resources) > 10:
        total_page = math.floor(len(resources)/10)

    # If we are on the first page
    if page == 1:
        previous_page = None
        if total_page == 1:
            next_page = None
        else:
            next_page = page + 1

    # If we are on the last page
    elif page == total_page:
        previous_page = page - 1
        next_page = None

    # If more pages exist
    elif page < total_page:
        previous_page = page - 1
        next_page = page + 1

    # If we are past total pages
    else: # page > total_page
        previous_page = total_page
        next_page = None


    pages = {
        "first_page": '1',
        "previous_page": previous_page,
        "next_page": next_page,
        "last_page": total_page,
        "total_pages": total_page,
        "per_page": 10
    }

    return pages
