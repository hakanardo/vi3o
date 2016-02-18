"""
:mod:`vi3o.image` --- Image handling
====================================
"""

import PIL.Image
import numpy as np
import os
from vi3o import view

NEAREST = PIL.Image.NEAREST
BILINEAR = PIL.Image.BILINEAR
BICUBIC = PIL.Image.BICUBIC
ANTIALIAS = PIL.Image.ANTIALIAS


def imsave(img, filename, format=None):
    """
    Save the image *img* into a file named *filename*. If the fileformat is not specified
    in *format*, the filename extension will be used as *format*.
    """
    if format is None:
        format = filename.split('.')[-1]
    if format == 'jpg':
        format = 'jpeg'
    if img.dtype != 'B':
        img = np.minimum(np.maximum(img, 0), 255).astype('B')
    PIL.Image.fromarray(img).save(filename, format.lower())

def imsavesc(img, filename, format=None):
    """
    Rescales the intensities of the image *img* to cover the 0..255 range and then calls
    :func:`vi3o.image.imsave` to save it.
    """
    imsave(ptpscale(img), filename, format)

def imread(filename):
    """
    Load an image from the file *filename*.
    """
    return np.array(PIL.Image.open(filename))


def imscale(img, size, interpolation=NEAREST):
    """
    Scales the image *img* into a new size specified by *size*. It can either be a number
    specifying a factor that relates the old size of the new or a 2-tuple with new size as
    *(width, height)*.
    """
    if isinstance(size, float) or isinstance(size, int):
        size = (size * img.shape[1], size * img.shape[0])
    size = map(int, size)
    return np.array(PIL.Image.fromarray(img).resize(size, interpolation))

def imrotate(img, angle, center=None, size=None, interpolation=NEAREST):
    h, w = img.shape[:2]
    if center is None:
        center = (w/2, h/2)
    if size is None:
        size = (w, h)
    else:
        size = tuple(size)
    cx, cy = size[0] / 2, size[1] / 2
    s, c = np.sin(angle),  np.cos(angle)
    # data = [c, -s, -c*center[0] + s*center[1] + cx,
    #         s,  c, -s*center[0] - c*center[1] + cy]
    data = [c, -s, -c*cx + s*cy + center[0],
            s,  c, -s*cx - c*cy + center[1]]
    return np.array(PIL.Image.fromarray(img).transform(size, PIL.Image.AFFINE, data, interpolation))


def ptpscale(img):
    """
    Rescales (and translates) the intensities of the image *img* to cover the 0..255 range.
    """
    a, b = min(img.flat), max(img.flat)
    if a == b:
        return np.zeros_like(img)
    return (img - a) * (255.0 / (b - a))


def imshow(img):
    view(img, pause=True)

def imshowsc(img):
    view(img, scale=True, pause=True)

imview = imshow
imviewsc = imshowsc

class ImageDirOut(object):
    """
    Creates a directory called *dirname* for storing a sequence of images in the format
    specified by *format*. If *append* is not *True* (default) the content of the directory
    will be cleard if it excists.
    """
    def __init__(self, dirname, format='jpg', append=False):
        self.dirname = dirname
        self.format = format
        self.fcnt = 0
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        if append:
            self.fcnt = len(os.listdir(dirname))
        else:
            for fn in os.listdir(dirname):
                os.unlink(os.path.join(dirname, fn))

    def view(self, img):
        """
        Save the image *img* as *dirname/xxxxxxxx.format* where *xxxxxxxx* is an 8 digit
        sequence number.
        """
        imsave(img, os.path.join(self.dirname, '%.8d.%s' % (self.fcnt, self.format)), self.format)
        self.fcnt += 1

    def viewsc(self, img):
        """
        Rescales the intensities of the image *img* to cover the 0..255 range, and call
        :py:meth:`~vi3o.image.ImageDirOut.view` to save it.
        """
        self.view(ptpscale(img))




