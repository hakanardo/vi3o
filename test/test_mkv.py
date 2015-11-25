from py.test import raises
from vi3o.mkv import Mkv
import os

mydir = os.path.dirname(__file__)
test_mkv = os.path.join(mydir, "t.mkv")

def test_iter():
    timestamps = []
    pixels = []
    video = Mkv(test_mkv)
    if os.path.exists(test_mkv + '.idx'):
        os.unlink(test_mkv + '.idx')
    for i, img in enumerate(video):
        assert img.index == i
        timestamps.append(img.timestamp)
        pixels.append(img[20,30,1])
    assert len(timestamps) == 16
    assert timestamps[0] == 0.0 # FIXME: Use systeime
    assert timestamps[1] == 0.04
    assert pixels[:6] == [84, 85, 85, 84, 84, 86]

    assert video[1].timestamp == 1445859308.97
    assert video[2].index == 2
    assert video[0][20,30,1] == 84

    video2 = Mkv(test_mkv)
    assert video[3][20,30,1] == 86

    assert len(video)== 16
    with raises(IndexError):
        video[100]


def test_no_file():
    with raises(IOError):
        Mkv(test_mkv + 'not_there')

