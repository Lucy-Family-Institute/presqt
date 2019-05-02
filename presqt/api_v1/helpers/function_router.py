from presqt.osf.osf_functions.fetch import fetch_resources


class FunctionRouter(object):
    """
    This class acts as a router to allow dynamic function calls based on a given variable.

    Each attribute links to a function. Naming conventions are important. They are as follows:

    Target Resources List:
        {target_name}_list

    """
    osf_list = fetch_resources
