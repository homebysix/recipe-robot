# We're using this package as a module.
try:
    from FoundationPlist import *
except ImportError:
    print(
        "WARNING: using 'from plistlib import *' instead of "
        "'from FoundationPlist import *' in " + __name__
    )
    from plistlib import *
