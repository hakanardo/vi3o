from py.test import raises
from vi3o.mjpg import Mjpg
import os

mydir = os.path.dirname(__file__)
test_mjpg = os.path.join(mydir, "t.mjpg")

def test_iter():
    timestamps = []
    pixels = []
    video = Mjpg(test_mjpg)
    os.unlink(test_mjpg + '.idx')
    for i, img in enumerate(video):
        assert img.index == i
        timestamps.append(img.timestamp)
        pixels.append(img[20,30,1])
    assert timestamps[1] == 1445859308.97
    assert pixels[:7] == [84, 83, 84, 86, 86, 84, 84]

    assert video[1].timestamp == 1445859308.97
    assert video[2].index == 2
    assert video[0][20,30,1] == 84

    video2 = Mjpg(test_mjpg)
    assert video[3][20,30,1] == 86


def test_no_file():
    with raises(IOError):
        Mjpg(test_mjpg + 'not_there')

