from presqt.osf.functions.fetch import osf_fetch_resources, osf_fetch_resource
from presqt.osf.functions.transfer import osf_download_resource


class FunctionRouter(object):
    """
    This class acts as a router to allow dynamic function calls based on a given variable.

    Each attribute links to a function. Naming conventions are important. They must match the keys
    we keep in the target.json config file. They are as follows:

    Target Resources Collection:
        {target_name}_resource_collection

    Target Resource Detail:
        {target_name}_detail

    Target Resource Download:
        {target_name}_download

    """
    @classmethod
    def get_function(cls, target_name, action):
        """
        Extracts the getattr() function call to this class method so the code using this class
        is easier to work with.
        """
        return getattr(cls, '{}_{}'.format(target_name, action))

    osf_resource_collection = osf_fetch_resources
    osf_resource_detail = osf_fetch_resource
    osf_resource_download = osf_download_resource