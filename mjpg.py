try:
    from _mjpg import ffi, lib
except ImportError:
    from vi3o import build_mjpg
    from _mjpg import ffi, lib
import numpy as np

class Frame(np.ndarray):
    pass

class Mjpg(object):
    def __init__(self, filename, grey=False):
        self.filename = filename
        self.grey = grey
        open(filename).close()

    def __iter__(self):
        return MjpgIter(self.filename, self.grey)


class MjpgIter(object):
    def __init__(self, filename, grey=False):
        self.m = ffi.new("struct mjpg *")
        self.fcnt = 0
        if grey:
            r = lib.mjpg_open(self.m, filename, lib.IMTYPE_GRAY, lib.IMORDER_PLANAR)
            self.channels = 1
        else:
            r = lib.mjpg_open(self.m, filename, lib.IMTYPE_RGB, lib.IMORDER_INTERLEAVED)
            self.channels = 3
        if r != lib.OK:
            raise IOError("Failed to open: " + filename)

    def __iter__(self):
        self

    def next(self):
        r = lib.mjpg_next(self.m)
        if r != lib.OK:
            raise StopIteration

        img = np.frombuffer(ffi.buffer(self.m.pixels, self.m.width * self.m.height * self.channels), 'B')
        if self.channels == 1:
            shape = (self.m.height, self.m.width)
        else:
            shape = (self.m.height, self.m.width, self.channels)
        img = img.reshape(shape).view(type=Frame)
        img.timestamp = self.m.timestamp_sec + self.m.timestamp_usec / 1000000.0
        img.index = self.fcnt
        self.fcnt += 1
        return img

