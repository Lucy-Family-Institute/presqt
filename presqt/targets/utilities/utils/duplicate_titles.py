import re
import fnmatch

from natsort import natsorted


def get_duplicate_title(title, titles, duplicate_format):
    """
    If the target has an existing project with the same title, we need to alter it slightly.

    Parameters
    ----------
    title : str
        The title of the new project
    titles : list
        The list  of titles to look through
    duplicate_format : str
        The duplicate format expected of the target, include an asterisk in the place of the int
        Examples: '-PresQT*-', ' (PresQT*)'

    Returns
    -------
    The new title.
    """
    # Check for an exact match
    exact_match = title in titles
    # Find only matches to the formatting that's expected in our title list
    duplicate_project_pattern = "{}{}".format(title, duplicate_format)
    duplicate_project_list = fnmatch.filter(titles, duplicate_project_pattern)

    if exact_match and not duplicate_project_list:
        return ("{}{}".format(title, duplicate_format.replace('*', '1')))

    elif duplicate_project_list:
        # Just build a list of the last numbers in the string and the last special character,
        # natsort unfortunately takes into account numbers in duplicate projects....so if we transfer 
        # or upload 'ProjectNine_-PresQT3-' but we already have 'ProjectNine_-PresQT3--PresQT1-' on
        # the target, natsort would set the next entry at 'ProjectNine_-PresQT3--PresQT4-'
        duplicate_project_list_numbers = [
            number.rpartition("PresQT")[2] for number in duplicate_project_list]
        highest_duplicate_project = natsorted(duplicate_project_list_numbers)
        # findall takes a regular expression and a string, here we pass it the last number in
        # highest duplicate project, and it is returned as a list. int requires a string as an
        # argument, so the [0] is grabbing the only number in the list and converting it.
        highest_number = int(re.findall(r'\d+', highest_duplicate_project[-1])[0])

        return ("{}{}".format(title, duplicate_format.replace('*', str(highest_number + 1))))

    return title
