from vi3o import Video
import os

mydir = os.path.dirname(__file__)
test_mjpg = os.path.join(mydir, "t.mjpg")
systime_mkv = os.path.join(mydir, "systime.mkv")


def test_video():
    assert Video(test_mjpg)[1].systime == 1445859308.97
    assert Video(systime_mkv)[1].systime == 1448984844.2525
