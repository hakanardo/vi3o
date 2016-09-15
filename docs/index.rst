vi3o - VIdeo and Image IO
=========================

Utility for loading/saving/displaying video and images. It gives random access
to the video frames. For recordings origination from Axis cameras in mjpg (in
http multipart format) or H264 (in .mkv format) the camera system time at the
time of capture is provided as a system timestamp for each frame.

To get system timestamps in H.264 recordings "User data" has to be enabled. It
is found by clicking "Setup", "System Options", "Advanced", "Plain Config" and
choosing "Image" followed by "Select group".

Status
======

Work in progress...

Installation
============

First, install some dependencies:

    .. code-block:: bash

        sudo apt-get install libjpeg62-turbo-dev libavcodec-dev libswscale-dev

Then there are a few different ways to install vi3o:

* Use pip:

    .. code-block:: bash

        sudo pip install vi3o

* or get the source code via the `Python Package Index`__.

.. __: http://pypi.python.org/pypi/vi3o

* or get it from `Github`_:

    .. code-block:: bash

      git clone https://github.com/hakanardo/vi3o.git
      cd vi3o
      sudo python setup.py install

.. _`Github`: https://github.com/hakanardo/vi3o


Whats new
=========

v0.5.2
------
* Slightly lighter background color behind images in DebugView to distinguish black backgrounds from outside image.
* Support for reading system timestamps from more recnt Axis cameras.
* Added a OpenCV fallback to allow unknown video formats to handled as `Video` object even if there are no system timestamps.
* Fixed a segfault when parsing broken or truncated mkv files.

v0.5.0
------
* Added :class:`vi3o.netcam.AxisCam` for reading video directly from Axis camera
* Add systimes property to Mkv and SyncedVideos to get a list of all system timestamps without decoding the frames.
* Switch to setuptools for proper handing of cffi dependency
* Remove numpy dependency during setup
* Dont try to decode truncated mkv frames

v0.4.0
------

* Allow negative indexes to wrap around in `Video` objects.
* Added :class:`vi3o.SyncedVideos` for syncornizing videos using `systime`.
* Support for showing images of different size side by side in the debug viewer.
* Support for showing images of different size one after the other in the debug viewer.
* Move the generated .idx files to the user .cache dir
* Regenerate the .idx files if the video is modfied
* Added :func:`vi3o.image.imrotate`.
* Added :func:`vi3o.image.imshow`.
* Added support for greyscale mjpg files.

Overview
========

Video recordings are are handled using *Video* objects, which are sliceable to
provide video object representing only part of the entire file,

.. code-block:: python

    from vi3o import Video

    recoding = Video("myfile.mkv")
    monochrome = Video("myfile.mkv", grey=True)

    first_part = recoding[:250]
    last_part = recoding[-250:]
    half_frame_rate = recoding[::2]
    backwards = recoding[::-1]

The video object can be used to iterate over the frames in the video,

.. code-block:: python

    for frame in recoding:
        ...

It also supoprts random access to any frame,

.. code-block:: python

    first_frame = recoding[0]
    second_frame = recoding[1]
    last_frame = recoding[-1]

The frame objects returned are numpy ndarray subclasses with a few extra properties:

     - *frame.index* - The index of the frame within in the video (i.e *video[frame.index] == frame*)
     - *frame.timestamp* - The timestamp of the frame as a float in seconds
     - *frame.systime* - The system timestamp specifying when the frame was aquired (a float of seconds elapsed since the Epoch, 1970-01-01 00:00:00 +0000).

The video frames can be displayed using the debug viewer,

.. code-block:: python

    from vi3o import Video, view

    for img in Video("myfile.mkv"):
        view(img)

This opens a window showing the video which can be controlled using:

    - Space - pauses and unpases
    - Enter - step forward a single frame if paused
    - Mouse wheel - zoomes in/out the video
    - Click and drag - pan around in the video
    - z - zoomes video to fit the window
    - f - toggles fullscreen mode
    - d - starts pdb debugger
    - s - Toggle enforced rescaling of all images into the 0..255 range

To show multiple images side by side in the window, call :func:`vi3o.flipp` to start colled images
and then once more to show the collected images and restart the collecting:

.. code-block:: python

    from vi3o import Video, view, flipp

    for img in Video("myfile.mkv"):
        flipp()

        brighter = 2 * img
        darker = 0.5 * img

        view(img)
        view(brighter)
        view(darker)

It is also possible to list all timestamps in a video without decoding the image data using:

.. code-block:: python

    from vi3o import Video

    Video("myfile.mkv").systimes

Modules
=======


.. automodule:: vi3o
   :members:
   :imported-members:

.. automodule:: vi3o.image
   :members:

.. automodule:: vi3o.netcam
   :members:


Comments and bugs
=================

There is a `mailing list`_ for general discussions and an `issue tracker`_ for reporting bugs and a `continuous integration service`_ that's running tests.

.. _`issue tracker`: https://github.com/hakanardo/vi3o/issues
.. _`mailing list`: https://groups.google.com/forum/#!forum/vi3o
.. _`continuous integration service`: https://travis-ci.org/hakanardo/vi3o

