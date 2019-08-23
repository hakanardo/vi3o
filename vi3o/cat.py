import collections
from glob import glob

import vi3o
from vi3o import mjpg
from vi3o import utils
from vi3o import compat

_VideoBlock = collections.namedtuple(
    "_VideoBlock", ["video", "timestamp_offset", "systime_offset"]
)


class VideoCat(object):
    """
    Concatenates multiple video files into a single video object. The *videos* parameter
    is a list of videos to be concatenated. It can either be a list of filenames or a list
    of other *Video* objects. Typical usage:

    .. code-block:: python

        from vi3o import VideoCat

        for img in VideoCat(['part1.mkv', 'part2.mkv']):
            ...

    """

    def __init__(self, videos, **kwargs):
        self._videos = []
        self._length = 0

        for values in videos:
            timestamp_offset, systime_offset = None, None

            try:
                vid, timestamp_offset, systime_offset = values
            except ValueError:
                vid = values

            if isinstance(vid, compat.basestring):
                vid = vi3o.Video(vid, **kwargs)

            if isinstance(vid, mjpg.Mjpg) and (
                timestamp_offset is not None or systime_offset is not None
            ):
                # TODO: Provide an implementation for mjpg movies that has the same
                #       behaviour w.r.t systime and timestamp as the Mkv implementation
                raise NotImplementedError()

            self._length += len(vid)
            self._videos.append(_VideoBlock(vid, timestamp_offset, systime_offset))

        self._systimes = []  # type: List[float]
        for blk in self._videos:
            if blk.systime_offset is None:
                self._systimes.extend(blk.video.systimes)
            else:
                self._systimes.extend(
                    (
                        blk_frame[0] / 1.0e6 + blk.systime_offset
                        for blk_frame in blk.video.frame
                    )
                )

    def __len__(self):
        return self._length

    def __iter__(self):
        frame_index = 0
        for blk in self._videos:
            for frame in blk.video:
                if blk.systime_offset is not None:
                    frame.systime = frame.timestamp + blk.systime_offset

                if blk.timestamp_offset is not None:
                    frame.timestamp += blk.timestamp_offset

                frame.index = frame_index
                frame_index += 1
                yield frame

    def __getitem__(self, item):
        if isinstance(item, slice):
            return utils.SlicedView(self, item, {"systimes": self._sliced_systimes})

        if isinstance(item, int):
            # Support negative indices
            if item < 0:
                item += self._length

            # Quick exit for excessive ranges
            if not 0 <= item < self._length:
                raise IndexError

            # Keep track of the requested frame index
            frame_index = item

            # Find the correct block
            for blk in self._videos:
                length = len(blk.video)
                # Break if the index lies in [previous_length, blk.cumulative_length)
                if item < length:
                    break
                item -= length

            else:
                # Unreachable
                raise RuntimeError("Oups")  # pragma: no cover

            # Collect the frame with the correct relative index
            frame = blk.video[item]  # pylint: disable=undefined-loop-variable

            # Update the systime of the frame
            if blk.systime_offset is not None:
                frame.systime = (
                    frame.timestamp
                    + blk.systime_offset  # pylint: disable=undefined-loop-variable
                )
            if blk.timestamp_offset is not None:
                frame.timestamp += blk.timestamp_offset

            frame.index = frame_index
            return frame

        raise TypeError

    @property
    def systimes(self):
        return self._systimes

    def _sliced_systimes(self, range_):
        return [self._systimes[i] for i in range_]

    @property
    def videos(self):
        """ Compatibility method """
        return [blk.video for blk in self._videos]


class VideoGlob(VideoCat):
    """
    Subclass of :class:`VideoCat` that is initiated with a :py:func:`glob.glob` wildcard string instead of
    a list of videos. The wildcard is expanded into a list of filenames that is the sorted before
    concatenated.
    """

    def __init__(self, pathname):
        videos = glob(pathname)
        videos.sort()
        VideoCat.__init__(self, videos)
