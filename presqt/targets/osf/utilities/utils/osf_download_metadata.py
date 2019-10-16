

def osf_download_metadata(file):
    """"
    For a given OSF file, generate the metadata expected.

    Parameters
    ----------
    file : obj
        The file object to generate metadata for.

    Returns
    -------
        The metadata dict
    """
    file_metadata = {
        "sourcePath": file.materialized_path,
        "title": file.title,
        "sourceHashes": file.hashes,
        "extra": {}}
    for key, value in file.__dict__.items():
        if key not in ['materialized_path', 'title', 'md5', 'sha256', 'hashes',
                       'session', 'kind', 'kind_name']:
            file_metadata['extra'][key] = value

    return file_metadata
