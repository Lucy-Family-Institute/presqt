def list_differences(list_one, list_two):
    """
    Compares two lists and returns a list of differences

    Parameters
    ----------
    list_one: list

    list_two: list

    Returns
    -------
    A list of differences between the two given lists.
    """

    return list(set([entry for entry in list_one if entry not in list_two]))