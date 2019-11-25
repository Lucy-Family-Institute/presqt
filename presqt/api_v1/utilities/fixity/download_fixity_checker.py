import hashlib

from presqt.api_v1.utilities.fixity.hash_generator import hash_generator

def download_fixity_checker(resource_dict):
    """
    Take a file in binary format and a dictionary of hashes and run a fixity check against the first
    one found that's supported by hashlib.

    Parameters
    ----------
    resource_dict: dict
        Dictionary that contains binary_file, hashes, title, and path

    Returns
    -------
    A dictionary object of the fixity check results.
    """
    fixity_obj = {
        'hash_algorithm': None,
        'source_hash': None,
        'presqt_hash': None,
        'fixity': None,
        'fixity_details': None,
        'title': resource_dict['title'],
        'path': resource_dict['path']
    }
    fixity_match = True

    for hash_algorithm, hash_value in resource_dict['hashes'].items():
        # If the current hash_value is not None and the hash algorithm is supported by hashlib
        # then this is the hash we will run our fixity checker against.
        if hash_value and hash_algorithm in hashlib.algorithms_available:
            # Run the file through the hash algorithm
            hash_hex = hash_generator(resource_dict['file'], hash_algorithm)

            fixity_obj['hash_algorithm'] = hash_algorithm
            fixity_obj['presqt_hash'] = hash_hex
            fixity_obj['source_hash'] = hash_value

            # Compare the given hash with the calculated hash.
            if hash_hex == hash_value:
                fixity_obj['fixity'] = True
                fixity_obj['fixity_details'] = 'Source Hash and PresQT Calculated hash matched.'
            else:
                fixity_obj['fixity'] = False
                fixity_obj['fixity_details'] = (
                    'Source Hash and PresQT Calculated hash do not match.')
                fixity_match = False
            break
    else:
        # If either there is no matching algorithms in hashlib or the provided hashes
        # don't have values then we assume fixity has remained and we calculate a new hash
        # using md5 to give to the user.
        h = hashlib.md5(resource_dict['file'])
        hash_hex = h.hexdigest()
        fixity_obj['hash_algorithm'] = 'md5'
        fixity_obj['presqt_hash'] = hash_hex
        fixity_obj['fixity_details'] = (
            'Either a Source Hash was not provided or the source hash algorithm is not supported.')
        fixity_match = False

    return fixity_obj, fixity_match
