import math


def get_page_total(total_number, per_page_number):
    """
    Given a total page number and number of items per page, calculate the page total

    Parameters
    ----------
    total_number: int
        Total number of pages
    per_page_number: int
        Number of items per page

    Returns
    -------
    Integer representing the total number of pages
    """
    return int(math.ceil(float(total_number)/per_page_number))