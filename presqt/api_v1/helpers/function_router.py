def get_osf_list(token):
    """
    PLACEHOLDER FUNCTION. WILL BE REMOVED WHEN OSF INTEGRATION OCCURS.
    """
    resources = [
        {'kind': 'container', 'container': 'someid', 'id': '3', 'kind_name': 'folder'},
        {'kind': 'item', 'container': 'someid2', 'id': '34', 'kind_name': 'file'},
    ]

    return resources

def get_osf_detail(token, resource_id):
    """
    PLACEHOLDER FUNCTION. WILL BE REMOVED WHEN OSF INTEGRATION OCCURS.
    """
    resource = {'title': 'hehehe', 'id': '3'}


    return resource

class FunctionRouter(object):
    """
    This class acts as a router to allow dynamic function calls based on a given variable.

    Each attribute links to a function. Naming conventions are important. They must match the keys
    we keep in the target.json config file. They are as follows:

    Target Resources Collection:
        {target_name}_resource_collection

    Target Resource Detail:
        {target_name}_detail

    """
    osf_resource_collection = get_osf_list
    osf_resource_detail = get_osf_detail