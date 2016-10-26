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

def imread(filename, repair=False):
    """
    Load an image from the file *filename*.
    """
    a =  PIL.Image.open(filename)
    if not repair:
        return np.array(a)
    try:
        a.load()
    except IOError as e:
        print("Warning: IOError while reading '%s': %s" % (filename, e))
    return np.array(a)


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

def imrotate(img, angle, center=None, size=None, interpolation=NEAREST, point=None):
    """
    Rotate the image, *img*, *angle* radians around the point *center* which defaults to
    the center of the image. The output image size is specified in *size* as *(width, height)*.
    If *point* is specifed as *(x, y)* it will be taken as a coordinate in the original image
    and be transformed into the corresponing coordinate in te output image and returned
    instead of the image.
    """
    if center is None:
        h, w = img.shape[:2]
        center = (w/2, h/2)
    if size is None:
        h, w = img.shape[:2]
        size = (w, h)
    else:
        size = tuple(size)
    cx, cy = size[0] / 2, size[1] / 2
    s, c = np.sin(angle),  np.cos(angle)
    data = [c, -s, -c*cx + s*cy + center[0],
            s,  c, -s*cx - c*cy + center[1]]
    if point is not None:
        a, b, c, d, e, f, _, _, _ = np.linalg.inv(np.vstack((np.reshape(data, (2, 3)), [0, 0, 1]))).flat
        x, y = point
        return a*x + b*y + c, d*x + e*y + f
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
    """
    Display the image *img* in the DebugViewer and pause the viewer with the image showing.
    """
    view(img, pause=True)

def imshowsc(img):
    """
    Rescales (and translates) the intensities of the image *img* to cover the 0..255 range.
    Then display the image *img* in the DebugViewer and pause the viewer with the image showing.
    """
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




