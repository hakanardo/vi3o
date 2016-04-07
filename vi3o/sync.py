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

    def __iter__(self):
        return SyncIter(self.videos)

class TimedIter(object):
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

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()


class SyncIter(object):
    def __init__(self, videos):
        self.videos = [TimedIter(v) for v in videos]
        start = max([v[0].systime for v in videos])
        frames = [v.next_timed(start) for v in self.videos]
        self.systime = sum([f.systime for f in frames]) / len(frames)
        self.intervall = max([(v[-1].systime - v[0].systime) / len(v) for v in videos])

    def next(self):
        self.systime += self.intervall
        return [v.next_timed(self.systime) for v in self.videos]

    def __iter__(self):
        return self


    def __next__(self):
        return self.next()
