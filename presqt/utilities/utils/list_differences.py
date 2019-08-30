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
    difference_list = list(set([entry for entry in list_one if entry not in list_two]))
    difference_list_two = list(set([entry for entry in list_two if entry not in list_one]))
    difference_list.extend(difference_list_two)

    return difference_list
