# Py2 compat
from __future__ import unicode_literals, print_function

import os
import sys

import pytest
import vi3o
from vi3o import cat
from test.util import _FakeVideo, itertools, mock



_LENGTHS = [5, 7, 3]
_BASE_OFFSET = 15

# Calculate offsets for blocks
_TIMESTAMP_OFFSETS = [0] + list(itertools.accumulate(_LENGTHS))
_SYSTIME_OFFSETS = [_BASE_OFFSET + x for x in _TIMESTAMP_OFFSETS]


# Systimes should be sequential with an offset
_EXPECTED_SYSTIMES = [_BASE_OFFSET + x for x in range(sum(_LENGTHS))]

# Timestamps should be sequential with 0 offset
_EXPECTED_TIMESTAMPS = [x for x in range(sum(_LENGTHS))]



@pytest.fixture(scope="function")
def mocked_mkv(monkeypatch):
    # Patch vi3o.mkv with Video object that returns
    # each of _Fake(l0), _Fake(l1), ..., _Fake(ln)
    monkeypatch.setattr(
        vi3o.mkv,
        "Mkv",
        mock.Mock(spec=vi3o.mkv.Mkv, side_effect=[_FakeVideo(l) for l in _LENGTHS]),
    )


@pytest.fixture(scope="function")
def videos(mocked_mkv):
    return [
        (vi3o.Video("hello.mkv"), timestamp_offset, systime_offset)
        for _, timestamp_offset, systime_offset in zip(
            _LENGTHS, _TIMESTAMP_OFFSETS, _SYSTIME_OFFSETS
        )
    ]


@pytest.fixture()
def videocat(videos):
    return cat.VideoCat(videos)


def test_videos_fixture(videos):
    for (video, _, _), expected_length in zip(videos, _LENGTHS):
        assert len(video) == expected_length
    assert len(videos) == len(_LENGTHS)


mydir = os.path.dirname(__file__)
test_mkvs = [os.path.join(mydir, f) for f in ["a.mkv", "b.mkv", "c.mkv"]]


def test_cat():
    all_videos = [vi3o.Video(v) for v in test_mkvs]
    frames = sum(len(v) for v in all_videos)
    video = cat.VideoCat(test_mkvs)

    systimes = []
    for fcnt, img in enumerate(video):
        assert img.index == fcnt
        systimes.append(img.systime)
    assert fcnt == frames - 1

    assert len(video) == frames
    assert video[3].systime == all_videos[0][3].systime
    assert video[-3].systime == all_videos[-1][-3].systime

    index = len(all_videos[0])
    cut = video[index - 2 : index + 2]
    assert len(cut) == 4
    assert cut[0].systime == all_videos[0][-2].systime
    assert cut[3].systime == all_videos[1][1].systime

    assert cut[0].pts == all_videos[0][-2].pts
    assert cut[3].pts == all_videos[1][1].pts == 60000

    assert video.systimes == systimes
    assert cut.systimes == systimes[index - 2 : index + 2]


def test_cat_iterator_raises_on_exhausted(videocat):
    iterator = iter(videocat)
    for length in _LENGTHS:
        for _ in range(length):
            next(iterator)

    # Now the iterator should be exhausted
    with pytest.raises(StopIteration):
        next(iterator)


def test_cat_iterator_correct_times(videocat):
    actual_systimes = []
    actual_timestamps = []
    for f in videocat:
        actual_systimes.append(f.systime)
        actual_timestamps.append(f.timestamp)

    assert actual_systimes == pytest.approx(_EXPECTED_SYSTIMES)
    assert actual_timestamps == pytest.approx(_EXPECTED_TIMESTAMPS)


def test_cat_correct_systimes(videocat):
    assert videocat.systimes == pytest.approx(_EXPECTED_SYSTIMES)


def test_cat_correct_length(videocat):
    assert len(videocat) == sum(_LENGTHS)


def test_cat_getitem_raises_typeerror(videocat):
    with pytest.raises(TypeError):
        _ = videocat["invalid value"]


def test_cat_getitem_backward_skipping(videocat):
    # Skip to block 2
    frame = videocat[sum(_LENGTHS[:2])]
    assert frame.systime != pytest.approx(_BASE_OFFSET)
    # Skip back to block 0
    frame = videocat[0]
    assert frame.systime == pytest.approx(_BASE_OFFSET)
    assert frame.timestamp == pytest.approx(0)


def test_cat_getitem_raises_indexerror_on_missing(videocat):
    with pytest.raises(IndexError):
        _ = videocat[sum(_LENGTHS)]

    with pytest.raises(IndexError):
        _ = videocat[-sum(_LENGTHS) - 1]


def test_cat_getitem_and_iterator_correspond(videocat):
    reference = list(videocat)
    for idx, expected in zip(range(0, sum(_LENGTHS)), reference):
        assert videocat[idx].systime == pytest.approx(expected.systime)
        assert videocat[idx].timestamp == pytest.approx(expected.timestamp)


def test_cat_getitem_negative_indices(videocat):
    length = sum(_LENGTHS)

    actual_systimes = list(videocat[idx].systime for idx in range(-length, 0))
    actual_timestamps = list(videocat[idx].timestamp for idx in range(-length, 0))
    assert actual_systimes == pytest.approx(_EXPECTED_SYSTIMES)
    assert actual_timestamps == pytest.approx(_EXPECTED_TIMESTAMPS)


def test_cat_getitem_slice_systimes(videocat):
    my_slice = slice(_LENGTHS[1] - 2, _LENGTHS[2])
    sliced_values = videocat[my_slice]

    assert sliced_values.systimes == pytest.approx(_EXPECTED_SYSTIMES[my_slice])


def test_cat_getitem_slice_values(videocat):
    my_slice = slice(_LENGTHS[1] - 2, _LENGTHS[2])

    actual_systimes = []
    actual_timestamps = []
    for f in videocat[my_slice]:
        actual_systimes.append(f.systime)
        actual_timestamps.append(f.timestamp)

    assert actual_systimes == pytest.approx(_EXPECTED_SYSTIMES[my_slice])
    assert actual_timestamps == pytest.approx(_EXPECTED_TIMESTAMPS[my_slice])


def test_cat_raises_on_mjpg():
    # With offsets it should raise
    video = mock.MagicMock(spec=vi3o.mjpg.Mjpg)
    with pytest.raises(NotImplementedError):
        _ = cat.VideoCat([(video, 0, 0)])

    # But not without
    _ = cat.VideoCat([video])


def test_cat_kwargs_forwarding(monkeypatch):
    my_mock = mock.MagicMock()
    monkeypatch.setattr(vi3o, "Video", my_mock)
    videocat = cat.VideoCat(["hello.mkv"], grey=True)
    my_mock.assert_called()
    my_mock.assert_called_with("hello.mkv", grey=True)
