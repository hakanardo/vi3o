"""
:mod:`vi3o.netcam` --- Live camera handling
===========================================
"""

import base64
import sys
import os

if sys.version_info > (3,):
    from io import BytesIO as StringIO
else:
    from cStringIO import StringIO

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from vi3o.image import imread
from vi3o.utils import Frame


class AxisCam(object):
    """
    Loads an mjpg stream directly from an Axis camera with hostname *ip* with the
    resolution *width*x*height* using the *username* and *password* as credntials.
    If *no_proxy* is True, the proxy settings from the environment will be ignored
    and any other keyword parameter will be passed on to the camera as a VAPIX
    parameter.
    """
    def __init__(self, ip, width=None, height=None, username=None, password=None, no_proxy=False, **kwargs):


        if no_proxy:
            os.environ['NO_PROXY'] = ip
            os.environ['no_proxy'] = ip
        mjpg_url = 'http://' + ip + '/mjpg/video.mjpg'
        if width is not None:
            mjpg_url += '?resolution=%dx%d' % (width, height)
        for k, v in kwargs.items():
            mjpg_url += '&%s=%s' % (k, v)

        r = requests.get(mjpg_url, auth=HTTPDigestAuth(username, password), stream=True)
        r.raise_for_status()

        self._fd = r.raw
        self.fcnt = 0

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        headers = {}
        while True:
            l = self._fd.readline()
            if not l:
                raise StopIteration
            if not l.strip() and headers:
                break
            if b':' in l:
                i = l.index(b':')
                headers[l[:i]] = l[i+1:].strip()

        data = self._fd.read(int(headers[b'Content-Length']))
        img = imread(StringIO(data)).view(Frame)
        img.index = self.fcnt
        self.fcnt += 1
        img.timestamp = img.systime = -1 # FIXME
        return img

if __name__ == '__main__':
    from vi3o import view
    for img in AxisCam("192.168.0.90", username="root", password="pass", no_proxy=True):
        view(img)