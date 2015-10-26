from vi3o.image import *
from util import TempDir
import numpy as np

def test_save_load():
    with TempDir() as d:
        img = np.zeros((320, 240, 3), 'B')
        img[10, 20] = 255
        imsave(img, os.path.join(d, "t1.jpg"), "jpg")
        imsave(img, os.path.join(d, "t2.png"))
        im1 = imread(os.path.join(d, "t1.jpg"))
        assert all(im1[10, 20] > 250)
        im2 = imread(os.path.join(d, "t2.png"))
        assert all(im2[10, 20] == 255)

        fimg = np.zeros((320, 240, 3))
        fimg[10, 20] = 0.1
        fimg[30, 40] = -0.1
        imsavesc(fimg, os.path.join(d, "t3.png"))
        im3 = imread(os.path.join(d, "t3.png"))
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

def test_imgdir():
    with TempDir() as d:
        img = np.zeros((320, 240, 3), 'B')
        out = ImageDirOut(d)
        out.view(img)
        out.view(img)
        out.view(img)
        assert len(os.listdir(d)) == 3

        out = ImageDirOut(d)
        out.view(img)
        out.view(img)
        assert len(os.listdir(d)) == 2

        out = ImageDirOut(d, append=True)
        out.view(img)
        out.view(img)
        assert len(os.listdir(d)) == 4
