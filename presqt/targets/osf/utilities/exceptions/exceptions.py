from presqt.utilities import PresQTResponseException


class OSFNotFoundError(PresQTResponseException):
    pass


class OSFForbiddenError(PresQTResponseException):
    pass