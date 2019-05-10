from presqt.osf.functions.fetch import osf_fetch_resources, osf_fetch_resource


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
    osf_resource_collection = osf_fetch_resources
    osf_resource_detail = osf_fetch_resource