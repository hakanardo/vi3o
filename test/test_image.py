from vi3o.image import *
from test.util import TempDir
import numpy as np
from py.test import raises
from vi3o.compat import pathlib
import io

mydir = os.path.dirname(__file__)
test_jpg = os.path.join(mydir, "00000000.jpg")
test_jpg2 = os.path.join(mydir, "img00012680.jpg")


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

def test_imsave_and_imread_pathlib():
    with TempDir() as d:
        img = np.zeros((320, 240, 3), 'B')
        img[10, 20] = 255
        path = pathlib.Path(f"{d}/t1.jpg")
        imsave(img, path, "jpg")
        imread(path).shape == (320, 240, 3)
        imsave(img, path)
        imread(path).shape == (320, 240, 3)


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

def test_imrotate():
    img = np.ones([12, 16], 'B') * 255
    # FIXME: Improve test by adding:
    # img[1, :] = img[10, :] = np.array(range(16)) * 10
    # img[:, 1] = img[:, 14] = np.array(range(12)) * 10
    img[0, :] = img[11, :] = 0
    img[:, 0] = img[:, 15] = 0

    rot = imrotate(img, 1.5708/2, [16, 0], [16*2, 12*2], NEAREST)
    # imwrite(rot, "/tmp/t.png")
    # os.system("xzgv /tmp/t.png")

    # pkt = imrotate(img, 1.5708, [16, 0], [16*2, 12*2], point=[16, 0])
    # assert all(np.round(pkt, 6) == [16, 12])

    cnt1 = cnt2 = 0
    for y in range(-12, 24):
        for x in range(-16, 32):
            rx, ry = imrotate(img, 1.5708/2, [16, 0], [16 * 2, 12 * 2], NEAREST, point=[x, y])
            rx, ry = int(round(rx)), int(round(ry))
            if 0 < rx < 16*2 and 0 < ry < 12*2:
                if 0 <= x < 16 and 0 <= y < 12:
                    assert rot[ry, rx] == img[y, x]
                    cnt1 += 1
                else:
                    assert rot[ry, rx] < 10
                    cnt2 += 1
    assert cnt1 > 10
    assert cnt2 > 10

    assert all(rot[:12].flat == 0)

def test_imread():
    img = imread(test_jpg)
    assert isinstance(img, np.ndarray)
    assert img.shape == (288, 360)
    with raises(IOError):
        img = imread(test_jpg2)
    img = imread(test_jpg2, True)
    assert isinstance(img, np.ndarray)
    assert img.shape == (240, 320, 3)

def test_imread_open_file():
    img = imread(open(test_jpg, "rb"))
    assert isinstance(img, np.ndarray)
    assert img.shape == (288, 360)

def test_imread_bytesio():
    bytesio = io.BytesIO(open(test_jpg, "rb").read())
    img = imread(bytesio)
    assert isinstance(img, np.ndarray)
    assert img.shape == (288, 360)

def test_imsave_bytesio():
    bytesio = io.BytesIO()
    imsave(np.zeros((10,10), dtype=np.uint8), bytesio, format="jpg")
    print(bytesio.getvalue())
    assert b"\xff\xd8" in bytesio.getvalue()  # Start of image
    assert b"\xff\xd9" in bytesio.getvalue()  # end of image
