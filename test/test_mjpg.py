from py.test import raises
from vi3o.mjpg import Mjpg
import os

mydir = os.path.dirname(__file__)
test_mjpg = os.path.join(mydir, "t.mjpg")

def test_iter():
    timestamps = []
    for i, img in enumerate(Mjpg(test_mjpg)):
        assert img.index == i
        timestamps.append(img.timestamp)
    assert timestamps[0] == 1445859308.97

def test_no_file():
    with raises(IOError):
        Mjpg(test_mjpg + 'not_there')

