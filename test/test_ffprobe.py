from py.test import raises

import os
from vi3o.ffprobe import FFProbe, FFProbeException
from vi3o.compat import pathlib
from vi3o.imageio import ImageioVideo

mydir = os.path.dirname(__file__)
test_mkv = os.path.join(mydir, "a.mkv")


def test_ffprobe():
    probe = FFProbe(test_mkv)
    assert len(probe.video) == 1
    assert len(probe.audio) == 0

    stream = probe.video[0]
    assert stream.codec_name == "h264"
    assert stream.pixel_format == "yuvj420p"
    assert stream.frame_size == (600, 800)
    assert stream.language == "eng"

    # 'Unsafe' fields does not have conversion, they are
    # raw from ffprobe:
    assert stream._width == '800'
    assert stream._height == '600'

    # Some fields like 'frames' is not available in
    # mkv video using ffprobe. We should add another
    # test video with mp4 format where we can test these
    # fields.
    with raises(FFProbeException):
        stream.frames


def test_ffprobe_no_such_file():
    test_path = os.path.join(mydir, "no_such_file.mp4")
    with raises(FileNotFoundError):
        FFProbe(test_path)


def test_imageio():
    v = ImageioVideo(test_mkv)

    # imageio ffmpeg can't find the length of the mkv video,
    # neither can ffprobe. This will fall back to the frame
    # counting method.

    # TODO: Decoding the video with the c implementation of the
    # mkv parser gives 1136 frames in video, decoding with
    # imageio-ffmpeg gives 1159 frames in video. All frames
    # seems OK visualy. Values in the frame does however differ
    # in all frames already from the start. Leaving this check
    # as is for now since the decoding issue is not related to
    # the frame counting issue.
    assert len(v) == 1159
