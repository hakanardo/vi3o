class SlicedView(object):
    def __init__(self, parent, indexes):
        self.parent = parent
        self.range = xrange(*indexes.indices(len(parent)))

    def __getitem__(self, item):
        return self.parent[self.range[item]]

    def __len__(self):
        return len(self.range)