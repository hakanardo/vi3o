from py.test import raises
import vi3o
from vi3o.mjpg import Mjpg
from vi3o.mkv import Mkv
from vi3o.utils import VideoFilter, Frame
from test.util import mock
import numpy as np
import os

mydir = os.path.dirname(__file__)
test_mjpg = os.path.join(mydir, "t.mjpg")
systime_mkv = os.path.join(mydir, "systime.mkv")

def test_slice_not_implemented_systime():
    """Systimes property not implemented for all videos

    propagate this correctly, but do allow slices..
    """
    class Dummy(mock.MagicMock):
        @property
        def systimes(self):
            raise NotImplementedError()
    video_mock = Dummy(spec_set=Mjpg)
    video_mock.__len__.return_value = 10
    video = VideoFilter(video_mock, lambda f: f[:])
    with raises(NotImplementedError):
        _ = video.systimes
    cut = video[2:4]
    assert len(cut) == 2
    with raises(NotImplementedError):
        _ = cut.systimes

def test_slice_implemented_systime():
    """Systimes property should follow a slice
    """
    video_mock = mock.MagicMock(spec_set=Mjpg)
    video_mock.__len__.return_value = 4
    video_mock.systimes = [1, 2, 4, 10]
    video = VideoFilter(video_mock, lambda f: f[:])
    assert video.systimes == [1, 2, 4, 10]
    cut = video[1:3]
    assert cut.systimes == [2, 4]

def test_iter():
    timestamps = []
    pixels = []
    video = VideoFilter(Mjpg(test_mjpg), lambda f: f[:50,:50])
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
    assert len(video)== 16
    with raises(IndexError):
        video[100]

@mock.patch.object(vi3o, 'Video')
def test_no_file(video_mock):
    def raise_error(filename, **kwargs):
        raise IOError("Mock error for %s" % filename)

    video_mock.side_effect = raise_error
    with raises(IOError):
        VideoFilter("dummy", lambda f: f)

def test_slice():
    video = VideoFilter(Mjpg(test_mjpg), lambda f: f)
    sub = video[2:5]
    assert [img[20,30,1] for img in sub] == [84, 86, 86]
    assert sub[1].timestamp == video[3].timestamp
    assert len(sub) == 3

def test_grey():
    video = VideoFilter(Mjpg(test_mjpg, grey=True), lambda f: f)
    for img in video:
        assert img.shape == (120, 160)

    video = VideoFilter(Mjpg(test_mjpg, grey=True), lambda f: f[:f.shape[0]//2])
    for img in video:
        assert img.shape == (60, 160)

def test_open_by_fname():
    video = VideoFilter(str(test_mjpg), lambda f: f)
    assert video[0].shape == (120, 160, 3)

def test_change_metadata():
    def offset_time(frame):
        frame.systime += 3600
        return frame

    pixels = []
    video1 = Mjpg(test_mjpg)
    video2 = VideoFilter(video1, offset_time)
    for img, img_filtered in zip(video1, video2):
        assert img.systime == img_filtered.systime - 3600
        assert img.timestamp == img_filtered.timestamp
        assert np.all(img[:7] == img_filtered[:7])

def test_change_metadata_on_copy():
    def offset_time(org_frame):
        frame = org_frame[:]
        frame.systime = org_frame.systime + 3600
        return frame

    pixels = []
    video1 = Mjpg(test_mjpg)
    video2 = VideoFilter(video1, offset_time)
    for img, img_filtered in zip(video1, video2):
        assert img.systime == img_filtered.systime - 3600
        assert img.timestamp == img_filtered.timestamp
        assert np.all(img[:7] == img_filtered[:7])

def test_mkv_systime():
    video = VideoFilter(Mkv(systime_mkv), lambda f: f[:])
    assert video[7].systime == 1448984844.6525
    t = [img.systime for img in video]
    assert t == video.systimes

    cut = video[10:20]
    assert t[10:20] == cut.systimes

def test_mkv_getitem():
    video = VideoFilter(Mkv(systime_mkv), lambda f: f[:])
    idx = 31
    for i in range(3):
        assert video[idx-1].index == idx-1
    for i in range(3):
        assert video[idx].index == idx
    for i in range(3):
        assert video[idx+1].index == idx+1

def _get_np_pointer(arr):
    return arr.__array_interface__["data"][0]

@mock.patch.object(vi3o, "Video")
def test_no_copy_filter(mocked_video):
    def filter_func(img):
        return img

    frm = Mjpg(test_mjpg)[0]
    mocked_video.return_value = [frm]
    
    video = VideoFilter("dummy", filter_func)
    assert _get_np_pointer(video[0]) == _get_np_pointer(frm)

@mock.patch.object(vi3o, "Video")
def test_copy_filter(mocked_video):
    def filter_func(img):
        return img.copy()

    frm = Mjpg(test_mjpg)[0]
    mocked_video.return_value = [frm]

    video = VideoFilter("dummy", filter_func)
    assert _get_np_pointer(video[0]) != _get_np_pointer(frm)
    assert video[0].timestamp == frm.timestamp
