"""
:mod:`vi3o.mjpg` --- Motion JPEG video loading
==============================================
"""

import json
import os, sys
from vi3o.utils import SlicedView, index_file, Frame
try:
    from vi3o._mjpg import ffi, lib
except ImportError as e:
    import warnings
    warnings.warn("Failed to import. Try to recompile/reinstall vi3o. " + str(e))

class Mjpg(object):
    """
    If a filename that ends with .mjpg is passed to :func:`vi3o.Video` this kind of object
    is returned. It has a few additional format specific properties:
    """
    def __init__(self, filename, grey=False):
        # Be compatible with pathlib.Path filenames
        filename = str(filename).encode('utf-8')
        self.filename = filename
        self.grey = grey
        open(filename).close()
        self._myiter = None
        self._index = None

    def __iter__(self):
        return MjpgIter(self.filename, self.grey)

    @property
    def myiter(self):
        if self._myiter is None:
            self._myiter = iter(self)
        return self._myiter

    @property
    def offset(self):
        if self._index is None:
            idx = index_file(self.filename, self.grey)
            if os.path.exists(idx):
                self._index = json.load(open(idx))
            else:
                self._index = [self.myiter.m.start_position_in_file for img in self.myiter]
                with open(idx, 'w') as fd:
                    json.dump(self._index, fd)
        return self._index

    @property
    def systimes(self):
        raise NotImplementedError

    def _sliced_systimes(self, range):
        return [self.systimes[i] for i in range]

    def __getitem__(self, item):
        if isinstance(item, slice):
            return SlicedView(self, item, {'systimes': self._sliced_systimes})
        if (item < 0):
            item += len(self)
        lib.mjpg_seek(self.myiter.m, self.offset[item])
        self.myiter.fcnt = item
        return self.myiter.next()

    def __len__(self):
        return len(self.offset)

    @property
    def hwid(self):
        """
        The Axis hardware id of the camera that made this recording.
        """
        self.myiter.next()
        return ffi.string(self.myiter.m.hwid)

    @property
    def serial_number(self):
        """
        The Axis serial number or mac address of the camera that made this recording.
        """
        self.myiter.next()
        return ffi.string(self.myiter.m.serial)

    @property
    def firmware_version(self):
        """
        The firmware version running in the camera when it made this recording.
        """
        self.myiter.next()
        return ffi.string(self.myiter.m.firmware)


class MjpgIter(object):
    def __init__(self, filename, grey=False):
        self.m = ffi.new("struct mjpg *")
        self.fcnt = 0
        if grey:
            r = lib.mjpg_open(self.m, filename, lib.IMTYPE_GRAY, lib.IMORDER_INTERLEAVED)
            self.channels = 1
        else:
            r = lib.mjpg_open(self.m, filename, lib.IMTYPE_RGB, lib.IMORDER_INTERLEAVED)
            self.channels = 3
        if r != lib.OK:
            raise IOError("Failed to open: " + filename)

    def __iter__(self):
        return self

    def next(self):
        r = lib.mjpg_next_head(self.m)
        if r != lib.OK:
            raise StopIteration
        if self.channels == 1:
            shape = (self.m.height, self.m.width)
        else:
            shape = (self.m.height, self.m.width, self.channels)
        img = Frame(shape, 'B')
        assert img.__array_interface__['strides'] is None
        self.m.pixels = ffi.cast('unsigned char *', img.__array_interface__['data'][0])

        r = lib.mjpg_next_data(self.m)
        if r != lib.OK:
            raise StopIteration

        # img = img.reshape(shape).view(type=Frame)
        img.timestamp = self.m.timestamp_sec + self.m.timestamp_usec / 1000000.0
        img.systime = img.timestamp
        img.index = self.fcnt
        self.fcnt += 1
        return img

    def __next__(self):
        return self.next()

    def __del__(self):
        lib.mjpg_close(self.m)

def jpg_info(filename):
    """
    Reads a single jpeg image from the file *filename* and extracts the Axis user data header.
    The information it contains is returned as a dict with the keys "hwid", "serial_numer" and
    "firmware_version".
    """
    if sys.version_info > (3,):
        filename = bytes(filename, "utf8")
    m = ffi.new("struct mjpg *")
    r = lib.mjpg_open(m, filename, lib.IMTYPE_GRAY, lib.IMORDER_PLANAR)
    lib.mjpg_next_head(m)
    res = {'hwid': ffi.string(m.hwid),
           'serial_number': ffi.string(m.serial),
           'firmware_version': ffi.string(m.firmware),
           'timestamp': m.timestamp_sec + m.timestamp_usec / 1000000.0}
    lib.mjpg_close(m)
    return res



