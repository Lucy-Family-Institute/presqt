from presqt.utilities import PresQTResponseException


def get_curate_nd_resource(resource_id, curate_nd_instance):
    """
    Get a CurateND resource based on a given id.

    Parameters
    ----------
    resource_id : str
        Resource ID to retrieve
    
    curate_nd_instance : CurateND class object
        Instance of the CurateND class we want to use to get the resource from.
    
    Returns
    -------
    The class object for the resource requested.
    """
    print(resource_id)
    try:
        resource = curate_nd_instance.item(resource_id)
    except:
        pass
    else:
        return resource
