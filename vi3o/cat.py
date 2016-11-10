from glob import glob
from vi3o.utils import SlicedView
from vi3o import Video

class VideoCat(object):
    """
    Concatenates multiple video files into a single video object. The *videos* parameter
    is a list of videos to be concatenated. It can either be a list of filenames or a list
    of other *Video* objects. Typical usage:

    .. code-block:: python

        from vi3o import VideoCat

        for img in VideoCat(['part1.mkv', 'part2.mkv']):
            ...

    """
    def __init__(self, videos):
        if not videos:
            raise AttributeError("VideoCat can't concatinate an empty sequence")
        self.videos = [Video(v) if isinstance(v, str) else v for v in videos]

    def __iter__(self):
        fcnt = 0
        for v in self.videos:
            for img in v:
                img.index = fcnt
                fcnt += 1
                yield img

    def __len__(self):
        return sum(len(v) for v in self.videos)

    def __getitem__(self, item):
        if isinstance(item, slice):
            return SlicedView(self, item, {'systimes': self._sliced_systimes})
        if (item < 0):
            item += len(self)
        for v in self.videos:
            if item < len(v):
                return v[item]
            item -= len(v)

    @property
    def systimes(self):
        return sum((v.systimes for v in self.videos), [])

    def _sliced_systimes(self, range):
        return [self.systimes[i] for i in range]


class VideoGlob(VideoCat):
    """
    Subclass of :class:`VideoCat` that is initiated with a :py:func:`glob.glob` wildcard string instead of
    a list of videos. The wildcard is expanded into a list of filenames that is the sorted before
    concatenated.
    """
    def __init__(self, pathname):
        videos = glob(pathname)
        videos.sort()
        VideoCat.__init__(self, videos)