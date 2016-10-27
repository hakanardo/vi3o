import os
from vi3o import VideoCat, Video

mydir = os.path.dirname(__file__)
test_mkvs = [os.path.join(mydir, f) for f in ['a.mkv', 'b.mkv', 'c.mkv']]

def test_cat():
    all_videos = [Video(v) for v in test_mkvs]
    frames = sum(len(v) for v in all_videos)
    video = VideoCat(test_mkvs)

    systimes = []
    for fcnt, img in enumerate(video):
        assert img.index == fcnt
        systimes.append(img.systime)
    assert fcnt == frames - 1

    assert len(video) == frames
    assert video[3].systime == all_videos[0][3].systime
    assert video[-3].systime == all_videos[-1][-3].systime

    index = len(all_videos[0])
    cut = video[index-2:index+2]
    assert len(cut) == 4
    assert cut[0].systime == all_videos[0][-2].systime
    assert cut[3].systime == all_videos[1][1].systime

    assert cut[0].pts == all_videos[0][-2].pts
    assert cut[3].pts == all_videos[1][1].pts == 60000

    assert video.systimes == systimes
    assert cut.systimes == systimes[index-2:index+2]
