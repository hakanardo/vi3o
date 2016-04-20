import sys, os, hashlib
import numpy as np

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

def index_file(fn, extradata=None):
    stats = os.stat(fn)
    key = str((os.path.abspath(fn), stats.st_size, stats.st_mtime, extradata))
    key = hashlib.md5(key.encode()).hexdigest()
    path = os.path.join(os.path.expanduser('~'), ".cache", "vi3o", key + '.idx')
    d = os.path.dirname(path)
    if not os.path.exists(d):
        os.makedirs(d)
    return path
