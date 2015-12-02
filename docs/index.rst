vi3o - VIdeo and Image IO
=========================

Utility for loading/saving/displaying video and images. It gives random
access to mjpg and mkv video frames. For recordings origination from Axis
cameras the camera system time at the time of capture is provided as timestamp
for each frame.

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


Overview
========

.. code-block:: python

    from vi3o import Video
    import time

    rec = Video("myfile.mkv")

    for frame in rec:
        print time.localtime(frame.systime)

    subrec = rec[10:20]
    last_frame = rec[-1]


Modules
=======


.. automodule:: vi3o
   :members:

Comments and bugs
=================

There is a `mailing list`_ for general discussions and an `issue tracker`_ for reporting bugs and a `continuous integration service`_ that's running tests.

.. _`issue tracker`: https://github.com/hakanardo/vi3o/issues
.. _`mailing list`: https://groups.google.com/forum/#!forum/vi3o
.. _`continuous integration service`: https://travis-ci.org/hakanardo/vi3o

https://travis-ci.org/hakanardo/vi3o