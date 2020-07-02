"""
:mod:`vi3o.image` --- Image handling
====================================
"""

import PIL.Image
import PIL.ImageFile
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
    try:
        # filename might be an open file
        PIL.Image.fromarray(img).save(filename, format.lower())
    except AttributeError:
        # Try converting filename to a string to handle e.g. patlib2 paths
        PIL.Image.fromarray(img).save(str(filename), format.lower())

def imsavesc(img, filename, format=None):
    """
    Rescales the intensities of the image *img* to cover the 0..255 range and then calls
    :func:`vi3o.image.imsave` to save it.
    """
    imsave(ptpscale(img), filename, format)

class Silent: pass

def imread(filename, repair=False, convert=None):
    """
    Load an image from the file *filename*. If *repair* is True, attempts will be made to decode
    broken frames, in which case partially decoded frames might be returned. A warning is printed
    to standard output unless *repair* is set to :class:`vi3o.image.Silent`. To convert the image
    to a specific colorspace, set *convert* to the deciered pillow colormode.
    """
    try:
        # filename might be an open file
        a =  PIL.Image.open(filename)
    except AttributeError:
        # Try converting filename to a string to handle e.g. patlib2 paths
        a =  PIL.Image.open(str(filename))
    pillow_truncated_img = PIL.ImageFile.LOAD_TRUNCATED_IMAGES
    try:
        PIL.ImageFile.LOAD_TRUNCATED_IMAGES = False
        a.load()
    except IOError as e:
        if not repair:
            raise
        if repair is not Silent:
            print("Warning: IOError while reading '%s': %s" % (filename, e))
        PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True  # Allow partial decode if truncated images
        a.load()
    finally:
        PIL.ImageFile.LOAD_TRUNCATED_IMAGES = pillow_truncated_img
    if convert is not None:
        a = a.convert(convert)
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
    return imrotate_and_scale(img, angle, 1.0, center, size, interpolation, point)

def imrotate_and_scale(img, angle, scale, center=None, size=None, interpolation=NEAREST, point=None):
    """
    Rotate the image, *img*, *angle* radians around the point *center* which defaults to
    the center of the image. The output image size is specified in *size* as *(width, height)*.
    If *point* is specifed as *(x, y)* it will be taken as a coordinate in the original image
    and be transformed into the corresponing coordinate in te output image and returned
    instead of the image. Integer coordinates are considered to be at the centers of the
    pixels.
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
    data = [scale*d for d in data]
    data[2] += (1-scale) * center[0]
    data[5] += (1-scale) * center[1]
    if point is not None:
        a, b, c, d, e, f, _, _, _ = np.linalg.inv(np.vstack((np.reshape(data, (2, 3)), [0, 0, 1]))).flat
        x, y = point
        x += 0.5
        y += 0.5
        return a*x + b*y + c - 0.5, d*x + e*y + f - 0.5
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

imview = imshow
imviewsc = imshowsc
imload = imread
imwrite = imsave
