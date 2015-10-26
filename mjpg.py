try:
    from _mjpg import ffi, lib
except ImportError:
    from vi3o import build_mjpg
    from _mjpg import ffi, lib

try:
    import PIL.Image
    import Image as PILImage
    NEAREST = PILImage.NEAREST
    BILINEAR = PILImage.BILINEAR
    BICUBIC = PILImage.BICUBIC
    ANTIALIAS = PILImage.ANTIALIAS
except ImportError:
    pass


import numpy as np

class Image(np.ndarray):
    def to_pil(self):
        return PILImage.fromarray(self)

    def save(self, filename, format):
        if format == 'jpg':
            format = 'jpeg'
        self.to_pil().save(filename, format)

    def scale(self, shape, interpolation=None):
        if interpolation is None:
            interpolation = NEAREST
        if isinstance(shape, float) or isinstance(shape, int):
            shape = (shape * self.width, shape * self.height)
        shape = map(int, shape)
        return np.array(self.to_pil().resize(shape, interpolation)).view(type=Image)

    @property
    def width(self):
        return self.shape[1]

    @property
    def height(self):
        return self.shape[0]


class Mjpg(object):
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
        return self

    def next(self):
        r = lib.mjpg_next(self.m)
        if r != lib.OK:
            raise StopIteration

        img = np.frombuffer(ffi.buffer(self.m.pixels, self.m.width * self.m.height * self.channels), 'B')
        if self.channels == 1:
            shape = (self.m.height, self.m.width)
        else:
            shape = (self.m.height, self.m.width, self.channels)
        img = img.reshape(shape).view(type=Image)
        img.timestamp = self.m.timestamp_sec + self.m.timestamp_usec / 1000000.0
        img.index = self.fcnt
        self.fcnt += 1
        return img

