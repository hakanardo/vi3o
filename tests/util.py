import tempfile
import shutil
from contextlib import contextmanager
import sys

import itertools

# Python2 compatibility
if sys.version_info >= (3, 3, 0):
    import unittest.mock as mock
else:
    import mock

    # Provide an _accumulate function for Py2
    def _accumulate(vals):
        retval = 0
        for val in vals:
            retval += val
            yield retval

    itertools.accumulate = _accumulate

@contextmanager
def TempDir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

class _FakeVideo:
    def __init__(self, length):
        self._length = length
        # Note: 1.0e6 is an implementation detail of vi3o.mkv.Mkv
        self.frame = list((idx * 1.0e6, idx, idx) for idx in range(length))

    def __iter__(self):
        for idx in range(self._length):
            obj = mock.MagicMock()
            obj.timestamp = idx
            obj.systime = idx
            yield obj

    def __len__(self):
        return self._length

    def __getitem__(self, idx):
        if 0 <= idx < self._length:
            obj = mock.MagicMock()
            obj.timestamp = idx
            obj.systime = idx
            return obj

        raise IndexError