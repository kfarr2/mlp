import sys

from .base import *
from .local import *
if 'test' in sys.argv:
    from .test import *
