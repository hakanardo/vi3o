import cv2
from vi3o.utils import Frame

class CvVideo(object):
    def __init__(self, filename, grey=False):
        self.grey = grey
        self.capture = cv2.VideoCapture(filename)

    def __len__(self):
        return int(self.capture.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))

    def __next__(self):
        return self.next(self)

    def next(self):
        index = int(self.capture.get(cv2.cv.CV_CAP_PROP_POS_FRAMES))
        timestamp = self.capture.get(cv2.cv.CV_CAP_PROP_POS_MSEC) / 1000.0
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
        self.capture.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, item)
        return self.next()

    def __del__(self):
        self.capture.release()
