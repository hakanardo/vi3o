import sys, os, hashlib
import numpy as np
import vi3o
from vi3o import compat

if sys.version_info > (3,):
    xrange = range

class Frame(np.ndarray):
    pass

class SlicedView(object):
    def __init__(self, parent, indexes, properties=()):
        self.parent = parent
        self.range = xrange(*indexes.indices(len(parent)))
        self.properties = properties

    def __getitem__(self, item):
        return self.parent[self.range[item]]

    def __len__(self):
        return len(self.range)

    def __getattr__(self, item):
        if item in self.properties:
            return self.properties[item](self.range)
        return getattr(self.parent, item)

    def __getstate__(self):
        state = dict(self.__dict__)
        del state['properties'] # FIXME
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.properties = ()

class VideoFilter:
    """Apply a filter on the output frames from a video

    VideoFilter objects can be used as regular vi3o videos but applies a filter to
    the Frame object when iterating or accessing it.

    E.g, create a video that only is using the top half of the frames:

        .. code-block:: python

            video = VideoFilter(fname, lambda frame: frame[:frame.shape[0]//2])

    E.g. offset the timestamp of each frame by one hour:

        .. code-block:: python

            def offset_time(frame):
                frame.systime += 3600
                return frame

            video = VideoFilter(fname, offset_time)
    """

    def __init__(self, video, filter_function, **kwargs):
        if isinstance(video, compat.basestring):
            video = vi3o.Video(video, **kwargs)
        self.video = video
        self.filter_function = filter_function

    def _sliced_systimes(self, range):
        """Systimes property might not be implemented, depends on base video class
        """
        return [self.systimes[i] for i in range]

    def __iter__(self):
        for f in self.video:
            yield self._filter(f)

    def __len__(self):
        return len(self.video)

    def __getitem__(self, item):
        if isinstance(item, slice):
            try:
                return SlicedView(self, item, {"systimes": self._sliced_systimes})
            except AttributeError:
                return SlicedView(self, item)
        return self._filter(self.video[item])

    def __getattr__(self, name):
        return getattr(self.video, name)

    def _filter(self, org_frame):
        img = self.filter_function(org_frame)
        frame = copy_missing_metadata(img, org_frame)
        return frame

def copy_missing_metadata(dst_img, template_frame):
    """Copy missing meta data from template Frame object
    """
    def try_set_attribute(frame, attribute):
        # Try first to keep from the input image
        if hasattr(dst_img, attribute):
            setattr(frame, attribute, getattr(dst_img, attribute))
            return
        # Try to copy from the template frame
        # properties for meta data might differ with video type...
        if hasattr(template_frame, attribute):
            setattr(frame, attribute, getattr(template_frame, attribute))
            
    dst_frame = dst_img.view(Frame)
    for attribute in ("timestamp", "systime", "pts", "index"):
        try_set_attribute(dst_frame, attribute)
    return dst_frame

cache_dir = os.path.join(os.path.expanduser('~'), ".cache", "vi3o")

def index_file(fn, extradata=None):
    stats = os.stat(fn)
    key = str((os.path.abspath(fn), stats.st_size, stats.st_mtime, extradata))
    key = hashlib.md5(key.encode()).hexdigest()
    path = os.path.join(cache_dir, key + '.idx')
    d = os.path.dirname(path)
    try:
        os.makedirs(d)
    except OSError:
        pass
    return path
