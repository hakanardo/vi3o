import sys
import datetime

if sys.version_info >= (3, 3, 0):
    import pathlib

    basestring = (str, bytes)
else:
    import pathlib2 as pathlib

    basestring = basestring