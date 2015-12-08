__version_info__ = (0, 3, 2)
__version__ = '.'.join(str(i) for i in __version_info__)

def Video(filename, grey=False):
    if filename.endswith('.mkv'):
        from vi3o.mkv import Mkv
        return Mkv(filename, grey)
    elif filename.endswith('.mjpg'):
        from vi3o.mjpg import Mjpg
        return Mjpg(filename, grey)
    else:
        raise NotImplementedError("'%s' has unknown file extension." % filename)

def _get_debug_viewer(name):
    from vi3o.debugview import DebugViewer
    if name not in DebugViewer.named_viewers:
        DebugViewer.named_viewers[name] = DebugViewer(name)
    return DebugViewer.named_viewers[name]


def view(img, name='Default', scale=False):
    _get_debug_viewer(name).view(img, scale)

def viewsc(img, name='Default'):
    view(img, name, True)

def flipp(name='Default'):
    _get_debug_viewer(name).flipp()

