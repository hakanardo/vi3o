"""
    Interprets the storage format for recordings in AXIS video
    storage format,  e.g. video stored on a NAS or SD card.
 """
from __future__ import unicode_literals, print_function
import collections
import datetime
import sys
import xml.etree.ElementTree

import vi3o
from vi3o import mkv
from vi3o import cat
from vi3o import compat

if sys.version_info >= (3, 5, 0):
    from typing import Any, List, Union, Dict

# Representation of data in XML block of a recording
RecordingBlock = collections.namedtuple(
    "RecordingBlock", ["start", "stop", "filename", "status"]
)
# Representation of data in XML of recording
RecordingMetadata = collections.namedtuple(
    "RecordingMetadata",
    [
        "recording_id",
        "channel",
        "start",
        "stop",
        "blocks",
        "width",
        "height",
        "framerate",
    ],
)


def _parse_axis_xml_timestamp(string):
    # type: (str) -> float
    return compat.utc_datetime_to_epoch(
        datetime.datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%fZ")
    )


def _read_xml(path):
    # type: (pathlib.Path) -> Any
    tree = xml.etree.ElementTree.parse(str(path))
    return tree.getroot()


def _read_recording_block(path):
    # type: (pathlib.Path) -> RecordingBlock
    root = _read_xml(path)

    filename = path.parent / (path.stem + ".mkv")
    if not filename.exists():
        filename = path.parent / (path.stem + ".mjpg")

    if not filename.exists():
        raise compat.FileNotFoundError(
            "Could not find a video file for {}".format(path)
        )

    status = root.findall(".//Status")[0].text
    if status != "Complete":
        raise RuntimeError(
            '{}: Expected status "Complete", was: "{}"'.format(path, status)
        )

    return RecordingBlock(
        start=_parse_axis_xml_timestamp(root.findall(".//StartTime")[0].text),
        stop=_parse_axis_xml_timestamp(root.findall(".//StopTime")[0].text),
        status=status,
        filename=filename,
    )


def read_recording_xml(recording_xml):
    # type: (Union[str,pathlib.Path]) -> RecordingMetadata
    """
        Read metadata from an Axis recording from e.g. a SD card or a NAS

        .. code-block:: python

            import vi3o

            metadata = vi3o.read_recording_xml("/path/to/recording.xml")
            print("Width: {}, Height: {}".format(metadata.width, metadata.height))
            print("Number of blocks: {}".format(len(metadata.blocks)))
    """
    if isinstance(recording_xml, str):
        recording_xml = compat.pathlib.Path(recording_xml)

    if not recording_xml.is_file():
        raise compat.FileNotFoundError("recording.xml must be a file")

    root = _read_xml(recording_xml)

    try:
        blocks = []
        for pth in recording_xml.parent.glob("*/*.xml"):
            blocks.append(_read_recording_block(pth))

    except (ValueError, xml.etree.ElementTree.ParseError) as error:
        raise RuntimeError("Failure parsing block {}: {}".format(pth, error))
    blocks.sort()

    return RecordingMetadata(
        recording_id=root.attrib["RecordingToken"],
        channel=int(root.findall(".//SourceToken")[0].text),
        start=_parse_axis_xml_timestamp(root.findall(".//StartTime")[0].text),
        stop=_parse_axis_xml_timestamp(root.findall(".//StopTime")[0].text),
        width=int(root.findall(".//Width")[0].text),
        height=int(root.findall(".//Height")[0].text),
        framerate=float(root.findall(".//Framerate")[0].text),
        blocks=tuple(blocks),
    )


class Recording(object):
    """
        Load video from a folder containing a Axis recording from e.g.
        a SD card or a NAS

        Axis stores videos in a blocked format together with XML metadata.
        The XML metadata contains time information which may be used to
        deduce the wall time of the recordings should the video streams
        themselves lack the proper metadata.

        Either use the convenience method `vi3o.Video`

        .. code-block:: python

            import vi3o
            recording = vi3o.Video("/path/to/recording.xml")

        Or load metadata manually using `read_recording_xml`

        .. code-block:: python

            import vi3o
            metadata = vi3o.read_recording_xml("/path/to/recording.xml")
            recording = Recording(metadata)


    """

    def __init__(self, metadata, **kwargs):
        if not metadata.blocks:
            raise RuntimeError("No recordings discovered!")

        # Preprocessing of all video blocks in folder - this may take some time...
        videos = []  # type: List[_VideoBlock]
        timestamp_offset = 0
        for blk in metadata.blocks:
            # Note: Video raises OSError if file was not found
            filename = str(blk.filename)
            videos.append(
                cat._VideoBlock(
                    video=filename,
                    timestamp_offset=timestamp_offset,
                    systime_offset=blk.start,
                )
            )
            # The first frame in the next block will start at timestamp offset
            timestamp_offset += blk.stop - blk.start

        self._video = cat.VideoCat(videos, **kwargs)

    def __len__(self):
        return len(self._video)

    @property
    def systimes(self):
        # type: () -> List[float]
        """ Return the systimes of all frames in recording """
        return self._video.systimes

    def __iter__(self):
        return iter(self._video)

    def __getitem__(self, item):
        return self._video[item]
