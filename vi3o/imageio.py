from __future__ import division
import imageio, os

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

    def __len__(self):
        return len(self.reader)

    def __getitem__(self, item):
        if isinstance(item, slice):
            return SlicedView(self, item)
        img = self.reader.get_data(item)
        img.index = item
        img.timestamp = item / self.fps
        return img
