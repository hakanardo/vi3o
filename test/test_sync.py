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

    assert len(videos) == 105
    assert len(videos[:10]) == 10
    assert len(videos[-10:]) == 10

    for i in range(105):
        a, b, c = videos[i]
        assert systimes[i] == (a.systime, b.systime, c.systime)

    skip50 = videos[50:]
    for i in range(105-50):
        a, b, c = skip50[i]
        assert systimes[i+50] == (a.systime, b.systime, c.systime)


    last10 = videos[-10:]
    for i in range(10):
        a, b, c = last10[i]
        assert systimes[i + 95] == (a.systime, b.systime, c.systime)

    assert last10.videos is videos.videos

    assert last10.systimes == systimes[-10:]
    assert last10.indexes == videos.indexes[-10:]

