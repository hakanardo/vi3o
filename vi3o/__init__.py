__version_info__ = (0, 3, 1)
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
