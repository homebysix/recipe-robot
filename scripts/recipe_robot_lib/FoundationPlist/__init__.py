# We're using this package as a module.
from __future__ import print_function

from __future__ import absolute_import

try:
    from .FoundationPlist import *
except ImportError:
    print(
        "WARNING: using 'from plistlib import *' instead of "
        "'from FoundationPlist import *' in " + __name__
    )
    from plistlib import *
