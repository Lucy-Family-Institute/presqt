from .base import *

ALLOWED_HOSTS = ['presqt-prod.crc.nd.edu']

CORS_ORIGIN_ALLOW_ALL = False

CORS_ORIGIN_WHITELIST = (
    'https://presqt-prod.crc.nd.edu', )

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'graypy': {
            'level': 'DEBUG',
            'class': 'graypy.GELFTLSHandler',
            'host': 'prometheus-logging.crc.nd.edu',
            'port': 12201,
            'extra_fields': True,
            'facility': 'n/a',  # deprecated field
            'localname': 'https://presqt-prod.crc.nd.edu',
            'level_names': True,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'graypy'],
            'level': 'WARNING',
            'propagate': True,
        },
        'presqt': {
            'handlers': ['console', 'graypy'],
            'level': 'DEBUG',
            'propogate': True,
        },
    },
    "formatters": {
        "simple": {
            "format": "%(levelname)s: [%(name)s:%(lineno)s] %(message)s"
        }
    }
}

