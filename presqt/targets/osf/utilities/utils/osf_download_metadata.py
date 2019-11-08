

def osf_download_metadata(file):
    """"
    For a given OSF file, generate the extra metadata expected.

    Parameters
    ----------
    file : obj
        The file object to generate metadata for.

    Returns
    -------
        The metadata dict
    """
    extra_metadata = {}
    for key, value in file.__dict__.items():
        if key not in ['materialized_path', 'title', 'md5', 'sha256', 'hashes',
                       'session', 'kind', 'kind_name']:
            extra_metadata[key] = value

    return extra_metadata
