import os
from vi3o import SyncedVideos

mydir = os.path.dirname(__file__)
test_mkvs = [os.path.join(mydir, f) for f in ['a.mkv', 'b.mkv', 'c.mkv']]

def test_sync():
    count = 0
    videos = SyncedVideos(*test_mkvs)
    systimes = []
    for a, b, c in videos:
        assert abs(a.systime - b.systime) < 0.06
        assert abs(b.systime - c.systime) < 0.06
        assert abs(a.systime - c.systime) < 0.06
        count += 1
        systimes.append((a.systime, b.systime, c.systime))
    assert count == 105
    assert videos.systimes == systimes
