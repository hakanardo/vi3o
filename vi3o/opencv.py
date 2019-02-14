"""
:mod:`vi3o.opencv` --- Fallbacks on OpenCV functionality
========================================================
"""

import cv2
from vi3o.image import ptpscale
from vi3o.utils import Frame, SlicedView
import os
import numpy as np

for attr in ('CAP_PROP_FRAME_COUNT', 'CAP_PROP_POS_FRAMES', 'CAP_PROP_POS_MSEC'):
    if not hasattr(cv2, attr):
        setattr(cv2, attr, getattr(cv2.cv, 'CV_' + attr))

class CvVideo(object):
    def __init__(self, filename, grey=False):
        if not os.path.exists(filename):
            raise IOError("File not found: '%s'" % filename)
        self.grey = grey
        self.capture = cv2.VideoCapture(filename)

    def __len__(self):
        return int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))

    def __next__(self):
        return self.next()

    def next(self):
        index = int(self.capture.get(cv2.CAP_PROP_POS_FRAMES))
        timestamp = self.capture.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        ret, frame = self.capture.read()
        if not ret:
            raise StopIteration
        if self.grey:
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = img.view(Frame)
        img.index = index
        img.timestamp = timestamp
        return img


    def __iter__(self):
        return self

    def __getitem__(self, item):
        if isinstance(item, slice):
            return SlicedView(self, item)
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, item)
        return self.next()

    def __del__(self):
        self.capture.release()

class CvOut(object):
    """
     Video file output using the same interface as the DebugViewer, but encodes the output to a video file
     such as .avi or .mkv instead. The *filname* specified with be overwritten and the frame rate can be
     specified using the *fps* argument. The video will be encoded using H264 if available and fall back on
     DIVX if not. To ensure that the file is proberly closed, this object can be used as a context manager:

     .. code-block:: python

        from vi3o.opencv import CvOut

        with CvOut("result.avi") as avi:
            avi.view(frame1)
            avi.view(frame2)
            ...

    """
    def __init__(self, filename, fps=25):
        self.filename = filename
        self.video = None
        self.fps = fps

    def view(self, img, scale=False):
        if img.dtype == 'bool':
            img = img.astype('B')
        if scale:
            img = ptpscale(img)
        if img.dtype != 'B':
            img = np.minimum(np.maximum(img, 0), 255).astype('B')

        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        if self.video is None:
            height, width, _ = img.shape
            for codec in [875967048, 1482049860, -1]: #[cv2.cv.FOURCC(*"H264"), cv2.cv.FOURCC(*"DIVX"), -1]:
                self.video = cv2.VideoWriter(self.filename, codec, self.fps, (width, height))
                if self.video.isOpened():
                    break
        self.video.write(img)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __del__(self):
        if self.video:
            self.video.release()
        self.video = None

if __name__ == '__main__':
    import numpy as np
    avi = CvOut("/tmp/t.avi")
    for i in range(100):
        avi.view(np.zeros((480, 640, 3)))
    del avi
