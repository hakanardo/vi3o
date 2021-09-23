from __future__ import division
import imageio, os
from vi3o.utils import SlicedView
from vi3o import ffprobe

class ImageioVideo(object):
    def __init__(self, filename, grey=False):
        if not os.path.exists(filename):
            raise IOError("File not found: '%s'" % filename)
        if grey:
            raise NotImplementedError
        try:
            self.reader = imageio.get_reader(filename)
        except ValueError:
            self.reader = imageio.get_reader(filename, 'ffmpeg')
        self.fps = self.reader.get_meta_data()['fps']
        if self.fps == 0:
            self.fps = 25
        self.filename = filename
        self._nframes = None

    def __len__(self):
        if self._nframes is not None:
            return self._nframes
        try:
            nframes = self.reader._meta["nframes"]
            if nframes == float("inf"):
                # imageio-ffmpeg has problem with e.g. mp4 videos, test
                # ffprobe instead
                try:
                    nframes = ffprobe.FFProbe(self.filename).video[0].frames
                    if not nframes:
                        raise ValueError()
                except (IOError, IndexError, ValueError, ffprobe.FFProbeException):
                    # As a last fallback, try to step through all the frames and
                    # count them. This is very slow since it decodes all frame data..
                    nframes = self._count_frames()
        except (AttributeError, KeyError):
            # For legacy compatibility, not sure if this is needed or not...
            nframes = len(self.reader)
        self._nframes = nframes
        return nframes

    def __getitem__(self, item):
        if isinstance(item, slice):
            return SlicedView(self, item)
        img = self.reader.get_data(item)
        img.index = item
        img.timestamp = item / self.fps
        return img

    @property
    def systimes(self):
        return [i / self.fps for i in range(len(self))]

    def _count_frames(self):
        print("WARNING: Can't infer length of stream, trying to count...")
        self._nframes = sum(1 for _ in iter(self))
        return self._nframes
