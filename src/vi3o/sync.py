from vi3o.utils import SlicedView

from vi3o import Video


class SyncedVideos(object):
    """
        Synchronize a set of videos using the `systime` timestamps. Frames will be dropped
        to adjust the frame rate to match the video with the lowest frame rate. Initial
        and trailing parts of the videos where there are not frames from all vidos will be
        dropped. To for example play 3 videos syncronized side by side, use:

        .. code-block:: python

            from vi3o import SyncedVideos, view, flipp

            for a, b, c in SyncedVideos('a.mkv', 'b.mkv', 'c.mkv'):
                flipp()
                view(a)
                view(b)
                view(c)

        It is also possible to access random frames or slices:

        .. code-block:: python

            from vi3o import SyncedVideos

            recoding = SyncedVideos('a.mkv', 'b.mkv', 'c.mkv'):
            first_part = recoding[:250]
            last_part = recoding[-250:]
            half_frame_rate = recoding[::2]
            backwards = recoding[::-1]

        The input argument *filenames_or_videos* is a list of either file names or *Video* objects.



    """
    def __init__(self, *filenames_or_videos):
        self.videos = [Video(v) if isinstance(v, str) else v for v in filenames_or_videos]
        start = max([v[0].systime for v in self.videos])
        times = [TimedIter(v.systimes) for v in self.videos]
        frames = [v.next_timed(start) for v in times]
        self.start_systime = sum([f[1] for f in frames]) / len(frames)
        self.start_index = [f[0] for f in frames]
        self.intervall = max([(v[-1].systime - v[0].systime) / len(v) for v in self.videos])
        self._systimes = None
        self._indexes = None

    def __iter__(self):
        return SyncVideoIter(self.videos, self.start_index, self.start_systime - self.intervall, self.intervall)

    def _calc_index_times(self):
        times = [TimedIter(v.systimes) for v in self.videos]
        systime = self.start_systime
        self._index_times = []
        while True:
            try:
                self._index_times.append(tuple(t.next_timed(systime) for t in times))
            except IndexError:
                break
            systime += self.intervall
        self._indexes = [tuple(t[0] for t in it) for it in self._index_times]
        self._systimes = [tuple(t[1] for t in it) for it in self._index_times]

    @property
    def systimes(self):
        """
            Retunrs a list of systime timestamps without decoding any pixel data.
        """
        if self._systimes is None:
            self._calc_index_times()
        return self._systimes

    def _sliced_systimes(self, range):
        return [self.systimes[i] for i in range]

    @property
    def indexes(self):
        """
            Retunrs a list of frame indexes of the frames used in the synced stream.
        """
        if self._indexes is None:
            self._calc_index_times()
        return self._indexes

    def _sliced_indexes(self, range):
        return [self.indexes[i] for i in range]

    def __getitem__(self, item):
        if isinstance(item, slice):
            return SlicedView(self, item, {'systimes': self._sliced_systimes,
                                           'indexes': self._sliced_indexes})
        if (item < 0):
            item += len(self)
        idx = self.indexes[item]
        return [v[i] for i, v in zip(idx, self.videos)]

    def __len__(self):
        return len(self.indexes)

class TimedIter(object):
    def __init__(self, systimes):
        self.systimes = systimes
        self.prev = 0

    def next_timed(self, systime):
        if self.systimes[self.prev] < systime:
            while not (self.systimes[self.prev] <= systime <= self.systimes[self.prev+1]):
                self.prev += 1
            if systime - self.systimes[self.prev] > self.systimes[self.prev + 1] - systime:
                self.prev += 1
        return (self.prev, self.systimes[self.prev])

class TimedVideoIter(object):
    def __init__(self, video):
        self.video = iter(video)
        self.prev = next(self.video)

    def next_timed(self, systime):
        if self.prev.systime > systime:
            return self.prev
        img = next(self.video)
        while not (self.prev.systime <= systime <= img.systime):
            self.prev = img
            img = next(self.video)
        if systime - self.prev.systime > img.systime - systime:
            self.prev = img
            return img
        else:
            p = self.prev
            self.prev = img
            return p

class SyncVideoIter(object):
    def __init__(self, videos, start_index, start_systime, intervall):
        self.videos = [TimedVideoIter(v[i:]) for v,i in zip(videos, start_index)]
        self.systime = start_systime
        self.intervall = intervall

    def next(self):
        self.systime += self.intervall
        return [v.next_timed(self.systime) for v in self.videos]

    def __iter__(self):
        return self


    def __next__(self):
        return self.next()
