import json
import os, sys
from vi3o._mkv import ffi, lib
import numpy as np

from vi3o.utils import SlicedView


class Frame(np.ndarray):
    pass

class Mkv(object):
    def __init__(self, filename, grey=False):
        if sys.version_info > (3,):
            filename = bytes(filename, "utf8")
        self.filename = filename
        self.grey = grey
        open(filename).close()
        self._myiter = None
        self._index = None
        self.systime_offset = 0

        if os.path.exists(self.filename + b'.idx'):
            index = json.load(open(self.filename + b'.idx'))
            self.frame = index['frame']
            self.systime_offset = index['systime_offset']
        else:
            self.frame = []
            m = lib.mkv_open(self.filename)
            frm = ffi.new('struct mkv_frame *')
            while lib.mkv_next(m, frm):
                self.frame.append([frm.pts, frm.offset, frm.key_frame])
            self.frame.sort()
            self.systime_offset = iter(self).estimate_systime_offset()

            with open(self.filename + b'.idx', 'w') as fd:
                json.dump({'frame': self.frame,
                           'systime_offset': self.systime_offset}, fd)

    def __iter__(self):
        return MkvIter(self.filename, self.systime_offset, self.grey)

    @property
    def myiter(self):
        if self._myiter is None:
            self._myiter = iter(self)
        return self._myiter

    def __getitem__(self, item):
        if isinstance(item, slice):
            return SlicedView(self, item)
        keyindex = item
        while self.frame[keyindex][2] == 0:
            keyindex -= 1
            assert keyindex >= 0
        pts = self.frame[item][0]
        if keyindex > self.myiter.fcnt or item < self.myiter.fcnt:
            lib.mkv_seek(self.myiter.m, self.frame[keyindex][1])
        for img in self.myiter:
            if img.pts == pts:
                self.myiter.fcnt = item + 1
                img.index = item
                return img
        assert False

    def __len__(self):
        return len(self.frame)

class DecodeError(Exception):
    pass

class MkvIter(object):
    def __init__(self, filename, systime_offset, grey=False):
        self.m = lib.mkv_open(filename)
        self.systime_offset = systime_offset
        self.frm = ffi.new('struct mkv_frame *')
        self.out_of_packages = False
        self.largest_seen_timestamp = -1
        self.last_returned_timestamp = -1
        self.next_package()
        assert self.m.codec_private
        assert self.m.codec_private_len > 0
        self.p = lib.decode_open(self.m)
        self.fcnt = 0
        self.pts = ffi.new('uint64_t *')
        if grey:
            self.channels = 1
        else:
            self.channels = 3
        if not self.m:
            raise IOError("Failed to open: " + filename)

    def estimate_systime_offset(self):
        return lib.mkv_estimate_systime_offset(self.m)

    def __iter__(self):
        return self

    def next_package(self):
        if lib.mkv_next(self.m, self.frm):
            self.largest_seen_timestamp = max(self.largest_seen_timestamp, self.frm.pts)
        else:
            self.out_of_packages = True


    def next(self):
        assert self.m.width > 0
        if self.channels == 1:
            shape = (self.m.height, self.m.width)
        else:
            shape = (self.m.height, self.m.width, self.channels)

        img = Frame(shape, 'B')
        assert img.__array_interface__['strides'] is None
        pixels = ffi.cast('uint8_t *', img.__array_interface__['data'][0])

        while not self.out_of_packages or self.last_returned_timestamp < self.largest_seen_timestamp:
            r = lib.decode_frame(self.p, self.frm, pixels, self.pts, self.channels == 1)
            self.next_package()
            if r == 1:
                break
            elif r == -1:
                raise DecodeError
        else:
            raise StopIteration

        img.index = self.fcnt
        img.pts = self.pts[0]
        img.timestamp = float(img.pts) / 1000000.0
        img.systime = float(img.pts + self.systime_offset) / 1000000.0
        self.last_returned_timestamp = self.pts[0]
        self.fcnt += 1
        return img

    def __next__(self):
        return self.next()
