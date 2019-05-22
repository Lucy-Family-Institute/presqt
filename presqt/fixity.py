import hashlib

def fixity_checker(binary_file, hashes):
    """
    Take a file in binary format and a dictionary of hashes and run a fixity check against the first
    one found that's supported by hashlib.

    Parameters
    ----------
    binary_file : byte object
        File as a byte object.
    hashes : dictionary
        Dictionary of known hashes the file had in the target.
        Example:
            {
                'md5': '1f67b72a90b524873a26cd5d2671d0ef',
                'sha256': None
            }

    Returns
    -------
    A dictionary object of the fixity check results.
    """
    fixity_obj = {
        'hash_algorithm': None,
        'given_hash': None,
        'calculated_hash': None,
        'fixity': True
    }

    for hash_algorithm, hash_value in hashes.items():
        # If the current hash_value is not None and the hash algorithm is supported by hashlib
        # then this is the hash we will run our fixity checker against.
        if hash_value and hash_algorithm in hashlib.algorithms_available:
            # Run the file through the hash algorithm.
            h = hashlib.new(hash_algorithm)
            h.update(binary_file)
            hash_hex = h.hexdigest()

            fixity_obj['calculated_hash'] = hash_hex
            fixity_obj['given_hash'] = hash_value
            fixity_obj['hash_algorithm'] = hash_algorithm

            # Compare the given hash with the calculated hash.
            if hash_hex != hash_value:
                fixity_obj['fixity'] = False
            break
    else:
        # If either there is no matching algorithms in hashlib or the provided hashes
        # don't have values then we assume fixity has remained and we calculate a new hash
        # using md5 to give to the user.
        h = hashlib.md5(binary_file)
        hash_hex = h.hexdigest()
        fixity_obj['calculated_hash'] = hash_hex
        fixity_obj['hash_algorithm'] = 'md5'

    return fixity_obj