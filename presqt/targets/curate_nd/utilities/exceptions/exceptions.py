from presqt.utilities import PresQTResponseException


class CurateNDNotFoundError(PresQTResponseException):
    pass


class CurateNDForbiddenError(PresQTResponseException):
    pass
