import cv2, os
import numpy as np

windows = {}

def _on_mouse(event, x, y, flags, name):
    if event == cv2.EVENT_LBUTTONDOWN:
        print("Click:", x, y)

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

