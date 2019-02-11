from .base import *

#  Default Setting Overrides
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Load optional settings specific to the local system
# (for example, custom settings on a developer's system).
# The file "local.py" is excluded from version control.
try:
    from .local import *
except ImportError:
    pass
