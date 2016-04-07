from vi3o import Video
import numpy as np


class SyncedVideos(object):
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

class SyncIter1(object):
    def __init__(self, videos):
        start = max([v[0].systime for v in videos])
        self.video_iters = [iter(v) for v in videos]
        for v in self.video_iters:
            try:
                while v.next().systime < start:
                    pass
            except StopIteration:
                pass
        self.buffered = None

    def next(self):
        if self.buffered is None:
            self.buffered = [v.next() for v in self.video_iters]
        frames = [v.next() for v in self.video_iters]
        dt = [n.systime - o.systime for n,o in zip(frames, self.buffered)]
        print(dt)
        m = sum(f.systime for f in self.buffered) / len(self.buffered)
        print(m)
        offset = [abs(f.systime - m) for f in self.buffered]
        print(offset)

if False:
    a = [0, 1, 2, 3, 4, 5, 6, 7]
    b = [0.1, 0.2, 0.4, 1.4, 1.6, 1.8, 2.4, 3.4]

    def tst():
        i = j = 0
        while True:
            while j < len(b) and b[j] < a[i]:
                j += 1
                if j == len(b): return
            print(a[i], b[j])
            while i < len(a) and a[i] < b[j]:
                i += 1
                if i == len(a): return
            print(a[i], b[j])

    tst()
# alt = []
# if j>0:
#     alt.append(b[j-1])
# if j<len(b):
#     alt.append(b[j])
# print a[i], alt
