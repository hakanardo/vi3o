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

class CvOut(object):
    def __init__(self, filename, fps=25):
        self.filename = filename
        self.video = None
        self.fps = fps

    def view(self, img):
        if self.video is None:
            height, width, _ = img.shape
            for codec in [cv2.cv.FOURCC(*"H264"), cv2.cv.FOURCC(*"DIVX"), -1]:
                self.video = cv2.VideoWriter(self.filename, codec, self.fps, (width, height))
                if self.video.isOpened():
                    break
        self.video.write(img)

    def __del__(self):
        self.video.release()

if __name__ == '__main__':
    import numpy as np
    avi = CvOut("/tmp/t.avi")
    for i in range(100):
        avi.view(np.zeros((480, 640, 3), 'B'))
    del avi