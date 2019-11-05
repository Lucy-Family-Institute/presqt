class PresQTError(Exception):
    pass


class PresQTInvalidTokenError(PresQTError):
    pass


class PresQTResponseException(PresQTError):
    """
    Custom exception that adds 'data' and 'status_code' to the exception so when the exception is
    raised we can dynamically return the proper Response object.

    data must be a string that explains the error.
    status_code must be a valid rest_framework.status status code
    """
    def __init__(self, data, status_code):
        self.data = data
        self.status_code = status_code

class PresQTValidationError(PresQTResponseException):
    pass

