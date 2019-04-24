def get_osf_list(token):
    """
    PLACEHOLDER FUNCTION. WILL BE REMOVED WHEN OSF INTEGRATION OCCURS.
    """
    resources = [
        {'kind': 'folder', 'container': 'someid', 'id': '3', 'kind_name': 'da name'},
        {'kind': 'file', 'container': 'someid2', 'id': '34', 'kind_name': 'name!'},
    ]

    return resources

class FunctionRouter(object):
    """
    This class acts as a router to allow dynamic function calls based on a given variable.

    Each attribute links to a function. Naming conventions are important. They are as follows:

    Target Resources List:
        {target_name}_list

    """
    osf_list = get_osf_list


