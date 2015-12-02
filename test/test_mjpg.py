from py.test import raises
from vi3o.mjpg import Mjpg
import os

mydir = os.path.dirname(__file__)
test_mjpg = os.path.join(mydir, "t.mjpg")

def test_iter():
    timestamps = []
    pixels = []
    video = Mjpg(test_mjpg)
    if os.path.exists(test_mjpg + '.idx'):
        os.unlink(test_mjpg + '.idx')
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
    if os.path.exists(test_mjpg + '.idx'):
        os.unlink(test_mjpg + '.idx')
    test_iter()
    test_iter()

def test_no_file():
    with raises(IOError):
        Mjpg(test_mjpg + 'not_there')

def test_slice():
    video = Mjpg(test_mjpg)
    sub = video[2:5]
    assert [img[20,30,1] for img in sub] == [84, 86, 86]
    assert sub[1].timestamp == video[3].timestamp
    assert len(sub) == 3


