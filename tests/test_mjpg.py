from py.test import raises
from vi3o.mjpg import Mjpg, jpg_info
from vi3o.utils import index_file
import os
from vi3o.compat import pathlib

mydir = os.path.dirname(__file__)
test_mjpg = os.path.join(mydir, "t.mjpg")
test_jpg = os.path.join(mydir, "tst.jpg")

def test_iter():
    timestamps = []
    pixels = []
    video = Mjpg(test_mjpg)
    if os.path.exists(index_file(test_mjpg)):
        os.unlink(index_file(test_mjpg))
    for i, img in enumerate(video):
        assert img.index == i
        timestamps.append(img.timestamp)
        assert img.timestamp == img.systime
        pixels.append(img[20,30,1])
    assert len(timestamps) == 16
    assert timestamps[1] == 1445859308.97
    assert pixels[:7] == [84, 83, 84, 86, 86, 84, 84]

    assert video[1].timestamp == 1445859308.97
    assert video[2].index == 2
    assert video[0][20,30,1] == 84

    video2 = Mjpg(test_mjpg)
    assert video[3][20,30,1] == 86

    assert len(video)== 16
    with raises(IndexError):
        video[100]

def test_idx():
    if os.path.exists(index_file(test_mjpg)):
        os.unlink(index_file(test_mjpg))
    test_iter()
    test_iter()

def test_no_file():
    with raises(IOError):
        Mjpg(test_mjpg + 'not_there')

def test_mjpg_pathlib_open():
    _ = Mjpg(pathlib.Path(test_mjpg))

def test_slice():
    video = Mjpg(test_mjpg)
    sub = video[2:5]
    assert [img[20,30,1] for img in sub] == [84, 86, 86]
    assert sub[1].timestamp == video[3].timestamp
    assert len(sub) == 3

def test_jpg_info():
    assert jpg_info(test_jpg) == {'firmware_version': b'6.15.70',
                                  'hwid': b'72d',
                                  'serial_number': b'ac:cc:8e:02:b4:36',
                                  'timestamp': 1502961384.44}

def test_grey():
    from vi3o import view
    video = Mjpg(test_mjpg, grey=True)
    for img in video:
        assert img.shape == (120, 160)

