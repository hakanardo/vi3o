from vi3o import Video
import numpy as np


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


    """
    def __init__(self, *filenames):
        self.videos = [Video(fn) for fn in filenames]
        start = max([v[0].systime for v in self.videos])
        times = [TimedIter(v.systimes) for v in self.videos]
        frames = [v.next_timed(start) for v in times]
        self.start_systime = sum([f[1] for f in frames]) / len(frames)
        self.intervall = max([(v[-1].systime - v[0].systime) / len(v) for v in self.videos])

    def __iter__(self):
        return SyncVideoIter(self.videos, self.start_systime, self.intervall)

    @property
    def systimes(self):
        times = [TimedIter(v.systimes) for v in self.videos]
        systime = self.start_systime
        res = []
        while True:
            systime += self.intervall
            try:
                res.append(tuple(t.next_timed(systime)[1] for t in times))
            except IndexError:
                break
        return res


class TimedIter(object):
    def __init__(self, systimes):
        self.systimes = systimes
        self.prev = 0

    def next_timed(self, systime):
        while not (self.systimes[self.prev] <= systime <= self.systimes[self.prev+1]):
            self.prev += 1
        if systime - self.systimes[self.prev] > self.systimes[self.prev + 1] - systime:
            self.prev += 1
        return (self.prev, self.systimes[self.prev])

class TimedVideoIter(object):
    def __init__(self, video):
        self.video = iter(video)
        self.prev = self.video.next()

    def next_timed(self, systime):
        if self.prev.systime > systime:
            return self.prev
        img = self.video.next()
        while not (self.prev.systime <= systime <= img.systime):
            self.prev = img
            img = self.video.next()
        if systime - self.prev.systime > img.systime - systime:
            self.prev = img
            return img
        else:
            p = self.prev
            self.prev = img
            return p

class SyncVideoIter(object):
    def __init__(self, videos, start_systime, intervall):
        self.videos = [TimedVideoIter(v) for v in videos]
        self.systime = start_systime
        self.intervall = intervall

    def next(self):
        self.systime += self.intervall
        return [v.next_timed(self.systime) for v in self.videos]

    def __iter__(self):
        return self


    def __next__(self):
        return self.next()
