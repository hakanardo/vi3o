import sys
import datetime

if sys.version_info >= (3, 3, 0):
    import pathlib

    basestring = (str, bytes)

    def utc_datetime_to_epoch(dt):  # pylint: disable=invalid-name
        # Note that the parsed datetime object must be "aware" for datetime.timestamp()
        # to produce the expected result. This means that we must set the timezone to
        # UTC explicitly.
        return dt.replace(tzinfo=datetime.timezone.utc).timestamp()

    FileNotFoundError = FileNotFoundError
else:
    import pathlib2 as pathlib

    basestring = basestring

    def utc_datetime_to_epoch(dt):  # pylint: disable=invalid-name
        # Keep datetimes naive to avoid any inadvertent time zone conversions
        return (
            dt.replace(tzinfo=None) - datetime.datetime(1970, 1, 1)
        ).total_seconds() + dt.microsecond / 1.0e6

    class FileNotFoundError(OSError):
        pass
