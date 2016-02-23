import sys, os, hashlib
if sys.version_info > (3,):
    xrange = range

class SlicedView(object):
    def __init__(self, parent, indexes):
        self.parent = parent
        self.range = xrange(*indexes.indices(len(parent)))

    def __getitem__(self, item):
        return self.parent[self.range[item]]

    def __len__(self):
        return len(self.range)

def index_file(fn):
    stats = os.stat(fn)
    key = str((os.path.abspath(fn), stats.st_size, stats.st_mtime))
    key = hashlib.md5(key).hexdigest()
    path = os.path.join(os.path.expanduser('~'), ".cache", "vi3o", key + '.idx')
    d = os.path.dirname(path)
    if not os.path.exists(d):
        os.makedirs(d)
    return path
