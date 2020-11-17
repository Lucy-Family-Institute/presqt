from cryptography.fernet import Fernet

from config.settings.base import TOKEN_KEY


def decrypt_token(encrypted_token):
    """
    Decrypt the user token to use in target functions.
​
    Parameters
    ----------
    encrypted_token: str
        The user's encrypted token from the DB.
    """
    # Initialize FERNET...(Fernet is a symmetric encryption method which makes sure that the
    # message encrypted cannot be manipulated/read without the key.)
    f = Fernet(TOKEN_KEY)

    # Decrypt the token
    decrypted_token = f.decrypt(encrypted_token.encode()).decode()

    return decrypted_token
