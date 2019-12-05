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
