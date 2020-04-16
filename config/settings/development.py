from .base import *

#  Default Setting Overrides
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

CORS_ORIGIN_ALLOW_ALL = False

CORS_ORIGIN_WHITELIST = (
    'https://localhost:3000',
    'https://127.0.0.1:3000')

# Load optional settings specific to the local system
# (for example, custom settings on a developer's system).
# The file "local.py" is excluded from version control.
try:
    from .local import *
except ImportError:
    pass

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
            'localname': 'presqt-develop',
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
