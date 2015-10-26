from vi3o.image import *
from util import TempDir
import numpy as np

def test_save_load():
    with TempDir() as d:
        img = np.zeros((320, 240, 3), 'B')
        img[10, 20] = 255
        imsave(img, "t1.jpg", "jpg")
        imsave(img, "t2.png")
        im1 = imread("t1.jpg")
        assert all(im1[10, 20] > 250)
        im2 = imread("t2.png")
        assert all(im2[10, 20] == 255)

        fimg = np.zeros((320, 240, 3))
        fimg[10, 20] = 0.1
        fimg[30, 40] = -0.1
        imsave(fimg, "t3.png")
        im3 = imread("t3.png")
        assert all(im3[10, 20] == 255)
        assert all(im3[30, 40] == 0)
        assert all(im3[1, 2] == 127)





def test_scale():
    img = np.zeros((240, 320, 3), 'B')
    assert imscale(img, 2).shape == (480, 640, 3)
    assert imscale(img, (640, 480)).shape == (480, 640, 3)

    img = np.zeros((240, 320), 'B')
    assert imscale(img, 0.5).shape == (120, 160)
    assert imscale(img, (160, 120)).shape == (120, 160)
