class PresQTError(Exception):
    pass


class PresQTResponseException(PresQTError):
    """
    Custom exception that adds 'data' and 'status_code' to the exception so when the exception is
    raised we can dynamically return the proper Response object.
    """
    def __init__(self, data, status_code):
        self.data = data
        self.status_code = status_code

class PresQTValidationError(PresQTResponseException):
    pass


class PresQTAuthorizationError(PresQTResponseException):
    pass


class PresQTInvalidTokenError(PresQTError):
    pass