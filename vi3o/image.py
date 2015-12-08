"""
:mod:`vi3o.image` --- Image handling
====================================
"""

import PIL.Image
import numpy as np
import os

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


def imscale(img, shape, interpolation=NEAREST):
    """
    Scales the image *img* into a new size specified by *shape*. It can either be a number
    specifying a factor that relates the old size of the new or a 2-tuple with new size as
    *(width, height)*.
    """
    if isinstance(shape, float) or isinstance(shape, int):
        shape = (shape * img.shape[1], shape * img.shape[0])
    shape = map(int, shape)
    return np.array(PIL.Image.fromarray(img).resize(shape, interpolation))


def ptpscale(img):
    """
    Rescales (and translates) the intensities of the image *img* to cover the 0..255 range.
    """
    a, b = min(img.flat), max(img.flat)
    if a == b:
        return np.zeros_like(img)
    return (img - a) * (255.0 / (b - a))


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




