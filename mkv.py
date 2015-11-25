import json
import os

from _mkv import ffi, lib
import numpy as np

class Frame(np.ndarray):
    pass

class Mkv(object):
    def __init__(self, filename, grey=False):
        self.filename = filename
        self.grey = grey
        open(filename).close()
        self._myiter = None
        self._index = None

    def __iter__(self):
        return MkvIter(self.filename, self.grey)

    @property
    def myiter(self):
        if self._myiter is None:
            self._myiter = iter(self)
        return self._myiter

    @property
    def offset(self):
        if self._index is None:
            if os.path.exists(self.filename + '.idx'):
                self._index = json.load(open(self.filename + '.idx'))
            else:
                self._index = [self.myiter.m.start_position_in_file for img in self.myiter]
                with open(self.filename + '.idx', 'w') as fd:
                    json.dump(self._index, fd)
        return self._index

    def __getitem__(self, item):
        lib.mjpg_seek(self.myiter.m, self.offset[item])
        self.myiter.fcnt = item
        return self.myiter.next()

    def __len__(self):
        return len(self.offset)

class DecodeError(Exception):
    pass

class MkvIter(object):
    def __init__(self, filename, grey=False):
        self.m = lib.mkv_open(filename)
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
        img.timestamp = float(self.pts[0]) / 1000000.0
        self.last_returned_timestamp = self.pts[0]
        self.fcnt += 1
        return img

