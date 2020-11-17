from cryptography.fernet import Fernet

from config.settings.base import TOKEN_KEY


def encrypt_token(token):
    """
    Encrypt the user token to store in the DB.
​
    Parameters
    ----------
    token: str
        The user's token.
    """
    # Initialize FERNET...(Fernet is a symmetric encryption method which makes sure that the
    # message encrypted cannot be manipulated/read without the key.)
    f = Fernet(TOKEN_KEY)
    # Encode the token
    encoded_token = token.encode()
    # Encrypt the token
    encrypted_token = f.encrypt(encoded_token).decode()

    return encrypted_token
