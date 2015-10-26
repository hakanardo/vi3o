import cv2, os
import numpy as np

windows = {}

def _on_mouse(event, x, y, flags, name):
    if event == cv2.EVENT_LBUTTONDOWN:
        print "Click:", x, y

def view(img, name="Video"):
    if name not in windows:
        windows[name] = cv2.namedWindow(name)
        cv2.setMouseCallback(name, _on_mouse, name)
    if img.dtype != 'B':
        img = np.minimum(np.maximum(img, 0), 255).astype('B')
    cv2.imshow(name, img)
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):
            exit(0)
        elif key == ord(' '):
            view.paused = not view.paused
        elif key == ord('\n'):
            return
        if not view.paused:
            return

view.paused = False

class ImageDirOut(object):
    def __init__(self, dirname, format='jpg'):
        self.dirname = dirname
        self.format = format
        self.fcnt = 0
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        for fn in os.listdir(dirname):
            os.unlink(os.path.join(dirname, fn))

    def view(self, img):
        if img.dtype != 'B':
            img = np.minimum(np.maximum(img, 0), 255).astype('B')
        img.save(os.path.join(self.dirname, '%.8d.%s' % (self.fcnt, self.format)), self.format)
        self.fcnt += 1

    def viewsc(self, img):
        a, b = min(img.flat), max(img.flat)
        if a == b:
            b += 1
        img = ((img.astype('d') - a) * 255 / (b - a)).astype('B')
        self.view(img)
