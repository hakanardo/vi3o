""" Test the block stitching logic of Recording """
from __future__ import unicode_literals, print_function

import itertools
import sys

import pytest
import vi3o.compat as compat
from vi3o import recording

from test.util import _FakeVideo, itertools, mock

# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

_RECORDING_DATA = (
    '<Recording RecordingToken="20190812_113000_B27F_00408C18823A" >'
    "<RecordingGroup> </RecordingGroup>"
    "<SourceToken>4</SourceToken>"
    "<StartTime>2019-08-12T09:30:00.813188Z</StartTime>"
    "<StopTime>2019-08-12T09:45:00.945062Z</StopTime>"
    "<Content></Content>"
    '<Track TrackToken="Video">'
    "<VideoAttributes>"
    "<Width>1920</Width>"
    "<Height>2160</Height>"
    "<Framerate>25.00000</Framerate>"
    "<Framerate_fraction>25:1</Framerate_fraction>"
    "<Encoding>video/x-h264</Encoding>"
    "<Bitrate>0</Bitrate>"
    "</VideoAttributes>"
    "</Track>"
    "<Application>AxisCamera</Application>"
    "<CustomAttributes>"
    "<TriggerTrigger>Record video</TriggerTrigger>"
    "<TriggerName>Record</TriggerName>"
    "<TriggerType>triggered</TriggerType>"
    "</CustomAttributes>"
    "</Recording>"
)

_BLOCK_DATA = (
    '<RecordingBlock RecordingBlockToken="20190808_141501_32D4" >'
    "<RecordingToken>20190808_141501_1778_00408C18823D</RecordingToken>"
    "<StartTime>2019-08-08T12:15:01.338584Z</StartTime>"
    "<StopTime>2019-08-08T12:20:01.704260Z</StopTime>"
    "<Status>Complete</Status>"
    "</RecordingBlock>"
)




# Note that normally only one type of block exists in a recording
_BLOCK_XML_FN_A = "derp.xml"
_BLOCK_MKV_FN_A = "derp.mkv"

_BLOCK_XML_FN_B = "herp.xml"
_BLOCK_MKV_FN_B = "herp.mkv"

_LENGTHS = [5, 7, 3]
_BASE_OFFSET = 15

# Calculate offsets for blocks
_BLOCK_OFFSETS = [
    _BASE_OFFSET + val for val in ([0] + list(itertools.accumulate(_LENGTHS)))
]


# Systimes should be sequential with an offset
_EXPECTED_SYSTIMES = [_BASE_OFFSET + x for x in range(sum(_LENGTHS))]

# Timestamps should be sequential with 0 offset
_EXPECTED_TIMESTAMPS = [x for x in range(sum(_LENGTHS))]


@pytest.fixture(scope="function", autouse=True)
def patched_vi3o(monkeypatch):
    # Patch vi3o.mkv with Video object that returns
    # each of _Fake(l0), _Fake(l1), ..., _Fake(ln)
    monkeypatch.setattr(
        recording.vi3o.mkv,
        "Mkv",
        mock.Mock(side_effect=[_FakeVideo(l) for l in _LENGTHS]),
    )


@pytest.fixture()
def recording_xml_data(tmp_path):
    # Generate a believable example with the following layout:
    #
    # tmp_path/
    # |--folder/
    #    |-- _BLOCK_XML_FN_A
    #        _BLOCK_MKV_FN_A
    #  --folder2/
    #    |-- _BLOCK_XML_FN_B
    #     -- _BLOCK_MKV_FN_B
    #  -- recording.xml
    #
    # and return the filepaths
    recording_xml = tmp_path / "recording.xml"
    recording_xml.write_text(_RECORDING_DATA)

    folder_a = tmp_path / "folder"
    folder_a.mkdir()
    xml_a = folder_a / _BLOCK_XML_FN_A
    video_a = folder_a / _BLOCK_MKV_FN_A
    xml_a.write_text(_BLOCK_DATA)
    video_a.write_bytes(b"")

    folder_b = tmp_path / "folder2"
    folder_b.mkdir()
    xml_b = folder_b / _BLOCK_XML_FN_B
    video_b = folder_b / _BLOCK_MKV_FN_B
    xml_b.write_text(_BLOCK_DATA)
    video_b.write_bytes(b"")
    yield recording_xml, xml_a, video_a, xml_b, video_b


def test_read_recording_xml_parsing(recording_xml_data):
    # Test both pathlib and str interface
    recording_xml, _, _, _, _ = recording_xml_data
    for path in [recording_xml, str(recording_xml)]:
        metadata = recording.read_recording_xml(path)
        # Correct channel parsed
        assert metadata.channel == 4  # SourceToken
        # Correct number of blocks discovered
        assert len(metadata.blocks) == 2
        # Filename of block is the same as the XML
        assert _BLOCK_MKV_FN_A in str(metadata.blocks[0].filename)
        # Alphanumerically ordered blocks
        assert _BLOCK_MKV_FN_B in str(metadata.blocks[1].filename)


@pytest.fixture
def metadata_missing_blocks():
    return recording.RecordingMetadata(
        recording_id="id",
        channel=0,
        start=0.0,
        stop=0.0,
        width=0,
        height=0,
        framerate=25,
        blocks=[],
    )


@pytest.fixture
def mocked_metadata(tmp_path):
    filename = tmp_path / "some_filename.mkv"
    filename.write_bytes(b"")

    blocks = [
        recording.RecordingBlock(
            start=offset, stop=offset + length, filename=filename, status="Complete"
        )
        for offset, length in zip(_BLOCK_OFFSETS, _LENGTHS)
    ]
    yield recording.RecordingMetadata(
        recording_id="id",
        channel=0,
        start=_BASE_OFFSET,
        # The end of the video is the last of the block_offsets
        stop=_BLOCK_OFFSETS[-1],
        width=0,
        height=0,
        framerate=1,
        blocks=blocks,
    )


def test_read_recoding_xml_raises_on_missing_recording_xml(tmp_path):
    with pytest.raises(compat.FileNotFoundError):
        _ = recording.read_recording_xml(tmp_path)


def test_read_recording_xml_raises_on_invalid_block(recording_xml_data):
    recording_xml, xml_a, _, _, _ = recording_xml_data
    xml_a.write_bytes(b"")
    with pytest.raises(RuntimeError):
        recording.read_recording_xml(recording_xml)


def test_read_recording_xml_raises_on_missing_video_for_block(recording_xml_data):
    recording_xml, _, video_a, _, _ = recording_xml_data
    video_a.unlink()
    with pytest.raises(compat.FileNotFoundError):
        _ = recording.read_recording_xml(recording_xml)


def test_read_recording_xml_raises_on_incomplete_status(recording_xml_data):
    recording_xml, xml_a, _, _, _ = recording_xml_data

    xml_a.write_text(_BLOCK_DATA.replace("Complete", "Incomplete"))
    with pytest.raises(RuntimeError):
        _ = recording.read_recording_xml(recording_xml)


def test_recording_raises_on_mjpg(recording_xml_data):
    recording_xml, _, video_a, _, _ = recording_xml_data

    # Note: Below is necessary due to pathlib.Path.replace only being available in Python 3.3+
    video_a.unlink()
    new_video = video_a.parent / (str(video_a.stem) + ".mjpg")
    new_video.write_bytes(b"")
    with pytest.raises(NotImplementedError):
        _ = recording.Recording(recording.read_recording_xml(recording_xml))


def test_recording_raises_on_empty_blocks(metadata_missing_blocks):
    with pytest.raises(RuntimeError):
        _ = recording.Recording(metadata_missing_blocks)


def test_recording_iterator_correct_times(mocked_metadata):
    actual_systimes = []
    actual_timestamps = []
    for f in recording.Recording(mocked_metadata):
        actual_systimes.append(f.systime)
        actual_timestamps.append(f.timestamp)

    assert actual_systimes == pytest.approx(_EXPECTED_SYSTIMES)
    assert actual_timestamps == pytest.approx(_EXPECTED_TIMESTAMPS)


def test_recording_forwards_kwargs(monkeypatch, mocked_metadata):
    my_mock = mock.MagicMock()

    monkeypatch.setattr(recording.cat, "VideoCat", my_mock)

    _ = recording.Recording(mocked_metadata, grey=True)
    assert my_mock.called
    _, kwargs = my_mock.call_args
    assert "grey" in kwargs
