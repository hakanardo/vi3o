import base64
import urllib2
from cStringIO import StringIO

from vi3o.image import imread
from vi3o.utils import Frame


class AxisCam(object):
    def __init__(self, ip, width=None, height=None, username=None, password=None):
        mjpg_url = 'http://' + ip + '/mjpg/video.mjpg'
        if width is not None:
            mjpg_url += '?resolution=%dx%d' % (width, height)
        request = urllib2.Request(mjpg_url)
        if username:
            base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
            request.add_header("Authorization", "Basic %s" % base64string)
        self._fd = urllib2.urlopen(request)
        self.fcnt = 0

    def __iter__(self):
        return self

    def next(self):
        headers = {}
        while True:
            l = self._fd.readline()
            if not l:
                raise StopIteration
            if not l.strip() and headers:
                break
            if ':' in l:
                i = l.index(':')
                headers[l[:i]] = l[i+1:].strip()

        data = self._fd.read(int(headers['Content-Length']))
        img = imread(StringIO(data)).view(Frame)
        img.index = self.fcnt
        self.fcnt += 1
        img.timestamp = img.systime = -1 # FIXME
        return img

if __name__ == '__main__':
    from vi3o import view
    for img in AxisCam('10.2.3.125', 640, 360):
        view(img)