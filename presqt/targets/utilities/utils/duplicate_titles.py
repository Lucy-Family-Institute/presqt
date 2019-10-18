import re
import fnmatch

from natsort import natsorted


def get_duplicate_title(title, titles, target):
    """
    If the target has an existing project with the same title, we need to alter it slightly.

    Parameters
    ----------
    titles : list
        The list  of titles to look through
    target : str
        The target calling the function

    Returns
    -------
    The new title.
    """
    # Check for an exact match
    exact_match = title in titles
    # Find only matches to the formatting that's expected in our title list
    if target == 'osf':
        duplicate_format = " (PresQT*)"
    if target == 'github':
        duplicate_format = "-PresQT*-"

    duplicate_project_pattern = "{}{}".format(title, duplicate_format)
    duplicate_project_list = fnmatch.filter(titles, duplicate_project_pattern)

    if exact_match and not duplicate_project_list:
        if target == 'osf':
            return ("{} (PresQT1)".format(title))
        elif target == 'github':
            return ("{}-PresQT1-".format(title))

    elif duplicate_project_list:
        highest_duplicate_project = natsorted(duplicate_project_list)
        # findall takes a regular expression and a string, here we pass it the last number in
        # highest duplicate project, and it is returned as a list. int requires a string as an
        # argument, so the [0] is grabbing the only number in the list and converting it.
        highest_number = int(re.findall(r'\d+', highest_duplicate_project[-1])[0])

        if target == 'osf':
            return ("{} (PresQT{})".format(title, highest_number+1))
        elif target == 'github':
            return ("{}-PresQT{}-".format(title, highest_number+1))

    return title
