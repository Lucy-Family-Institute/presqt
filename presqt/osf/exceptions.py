from presqt.exceptions import PresQTResponseException


class OSFNotFoundError(PresQTResponseException):
    pass


class OSFForbiddenError(PresQTResponseException):
    pass