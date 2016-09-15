from py.test import raises
from vi3o.mkv import Mkv, lib, ffi
import os

from vi3o.utils import index_file

mydir = os.path.dirname(__file__)
test_mkv = os.path.join(mydir, "t.mkv")
systime_mkv = os.path.join(mydir, "systime.mkv")

def test_iter():
    timestamps = []
    pixels = []
    video = Mkv(test_mkv)
    if os.path.exists(index_file(test_mkv)):
        os.unlink(index_file(test_mkv))
    for i, img in enumerate(video):
        assert img.index == i
        timestamps.append(img.timestamp)
        pixels.append(img[20,30,1])
    assert len(timestamps) == 16
    assert timestamps[0] == 0.0 # FIXME: Use systeime
    assert timestamps[1] == 0.04
    assert pixels[:6] == [84, 85, 85, 84, 84, 86]

    pixels = [video[i][20,30,1] for i in range(6)]
    assert pixels == [84, 85, 85, 84, 84, 86]

    assert video[2].timestamp == 0.08
    assert video[1].timestamp == 0.04
    assert video[2].index == 2
    assert video[0][20,30,1] == 84

    video2 = Mkv(test_mkv)
    assert video[3][20,30,1] == 84

    assert len(video)== 16
    with raises(IndexError):
        video[100]

def test_idx():
    if os.path.exists(index_file(test_mkv)):
        os.unlink(index_file(test_mkv))
    test_iter()
    test_iter()

def test_no_file():
    with raises(IOError):
        Mkv(test_mkv + 'not_there')

def test_slice():
    video = Mkv(test_mkv)
    sub = video[2:5]
    assert [img[20,30,1] for img in sub] == [85, 84, 84]
    assert sub[1].timestamp == video[3].timestamp
    assert len(sub) == 3

def test_systime():
    video = Mkv(systime_mkv)
    assert video[7].systime == 1448984844.6525
    t = [img.systime for img in video]
    assert t == video.systimes

def test_getitem():
    video = Mkv(systime_mkv)
    idx = 31
    for i in range(3):
        assert video[idx-1].index == idx-1
    for i in range(3):
        assert video[idx].index == idx
    for i in range(3):
        assert video[idx+1].index == idx+1

def test_bad_file():
    fn = test_mkv + '_bad'
    for bad in ["\000", "\001"]:
        with open(fn, "w") as fd:
            fd.write(bad)
        m = lib.mkv_open(fn)
        frm = ffi.new('struct mkv_frame *')
        assert lib.mkv_next(m, frm) == 0
