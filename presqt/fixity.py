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
                'md5': 'Some Hash',
                'sha256': None
            }

    Returns
    -------
    A dictionary object of the fixity check results.
    """
    for hash_algorithm, hash_value in hashes.items():
        # If the current hash_value is not None and the hash algorithm is supported by hashlib
        # then this is the hash we will run our fixity checker against.
        if hash_value and hash_algorithm in hashlib.algorithms_available:
            # Run the file through the hash algorithm
            h = hashlib.new(hash_algorithm)
            h.update(binary_file)

            # Compare the given hash with the calculated hash.
            if h.hexdigest() == hash_value:
                # Fixity check has passed
                return {
                    'hash_algorithm': hash_algorithm,
                    'hash': hash_value,
                    'fixity': True
                }
            else:
                # Fixity check has failed.
                return {
                    'hash_algorithm': hash_algorithm,
                    'hash': hash_value,
                    'fixity': False
                }
    # If none of the provided hashes are supported by hashlib or the file didn't come with
    # any hashes to check against then we say fixity has passed.
    else:
        return {
                    'hash_algorithm': None,
                    'hash': None,
                    'fixity': True
                }
