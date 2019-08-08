

def compare_lists(list_one, list_two):
    """
    Compares two lists and returns a list of shared values between them.

    Parameters
    ----------
    list_one: list

    list_two: list

    Returns
    -------
    A list of matching items between the two given lists.
    """

    return [entry for entry in list_one if entry in list_two]