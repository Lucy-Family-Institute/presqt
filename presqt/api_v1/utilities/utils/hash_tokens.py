import hashlib


def hash_tokens(token):
    """
    Hash a user's token to securely store in process_info.

    Parameters
    ----------
    token : str
        The user's authorization token

    Returns
    -------
    The hashed token.
    """
    hashed_token = hashlib.sha256(token.encode())

    # Returns as a string of double length, containing only hexadecimal digits.
    return hashed_token.hexdigest()
