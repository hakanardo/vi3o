__version_info__ = (0, 3, 2)
__version__ = '.'.join(str(i) for i in __version_info__)

def Video(filename, grey=False):
    """
    Creates a *View* object representing the video in the file *filename*.
    See Overview above.
    """
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
    """
    Show the image *img* (a numpy array) in the debug viewer window named *name*.
    If *scale* is true the image intensities are rescaled to cover the 0..255
    range.
    """
    _get_debug_viewer(name).view(img, scale)

def viewsc(img, name='Default'):
    """
    Calls :func:`vi3o.view` with *scale=True*.
    """
    view(img, name, True)

def flipp(name='Default'):
    """
    After :func:`vi3o.flipp` is called, subsequent calls to :func:`vi3o.view` will no
    longer display the images directly. Instead they will be collected and concatinated.
    On the next call to :func:`vi3o.flipp` all the collected images will be displayed.
    """
    _get_debug_viewer(name).flipp()

