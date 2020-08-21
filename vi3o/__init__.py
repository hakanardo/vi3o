"""
:mod:`vi3o` ---  VIdeo and Image IO
====================================
"""

from .version import __version_info__, __version__

# FIXME: Turn into a Video base class that documents the interface

def Video(filename, grey=False):
    """
    Creates a *Video* object representing the video in the file *filename*.
    See Overview above.
    """
    # Be compatible with pathlib.Path filenames
    filename = str(filename)

    if filename.endswith('.mkv'):
        from vi3o.mkv import Mkv
        return Mkv(filename, grey)
    elif filename.endswith('.mjpg'):
        from vi3o.mjpg import Mjpg
        return Mjpg(filename, grey)
    elif filename.endswith('recording.xml'):
        from vi3o.recording import read_recording_xml, Recording
        return Recording(read_recording_xml(filename), grey=grey)
    else:
        from vi3o.imageio import ImageioVideo
        return ImageioVideo(filename, grey)


def _get_debug_viewer(name):
    from vi3o.debugview import DebugViewer
    if name not in DebugViewer.named_viewers:
        DebugViewer.named_viewers[name] = DebugViewer(name)
    return DebugViewer.named_viewers[name]


def view(img, name='Default', scale=False, pause=None):
    """
    Show the image *img* (a numpy array) in the debug viewer window named *name*.
    If *scale* is true the image intensities are rescaled to cover the 0..255
    range. If *pause* is set to True/False, the viewer is paused/unpaused after the
    image is displayed.
    """
    _get_debug_viewer(name).view(img, scale, pause=pause)

def viewsc(img, name='Default', pause=None):
    """
    Calls :func:`vi3o.view` with *scale=True*.
    """
    view(img, name, True, pause)

def flipp(name='Default', pause=None, aspect_ratio=None):
    """
    After :func:`vi3o.flipp` is called, subsequent calls to :func:`vi3o.view` will no
    longer display the images directly. Instead they will be collected and concatinated.
    On the next call to :func:`vi3o.flipp` all the collected images will be displayed.
    If *pause* is set to True/False, the viewer is paused/unpaused after the
    image is displayed.
    If aspect_ratio is set the images will be stacked in such a way that the total
    aspect ratio is close to aspect_ratio.
    """
    _get_debug_viewer(name).flipp(pause, aspect_ratio)

from vi3o.sync import SyncedVideos
from vi3o.cat import VideoCat, VideoGlob
