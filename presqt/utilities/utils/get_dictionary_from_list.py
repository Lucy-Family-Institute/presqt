def get_dictionary_from_list(list_to_search, key, search_value):
    """
    Find a dictionary in a list of dictionaries based on a certain key's value

    Parameters
    ----------
    list_to_search: list
        List of dictionaries to search in
    key: str
        The key in the dictionaries to look for the value
    search_value: str
        The key's value you are looking to match

    Returns
    -------
    Dictionary object we are searching for
    """
    for the_dict in list_to_search:
        if the_dict[key] == search_value:
            return the_dict