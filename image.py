import PIL.Image
import numpy as np
import os

NEAREST = PIL.Image.NEAREST
BILINEAR = PIL.Image.BILINEAR
BICUBIC = PIL.Image.BICUBIC
ANTIALIAS = PIL.Image.ANTIALIAS


def imsave(img, filename, format=None):
    if format is None:
        format = filename.split('.')[-1]
    if format == 'jpg':
        format = 'jpeg'
    if img.dtype != 'B':
        img = np.minimum(np.maximum(img, 0), 255).astype('B')
    PIL.Image.fromarray(img).save(filename, format.lower())

def imsavesc(img, filename, format=None):
    imsave(ptpscale(img), filename, format)

def imread(filename):
    return np.array(PIL.Image.open(filename))


def imscale(img, shape, interpolation=NEAREST):
    if isinstance(shape, float) or isinstance(shape, int):
        shape = (shape * img.shape[1], shape * img.shape[0])
    shape = map(int, shape)
    return np.array(PIL.Image.fromarray(img).resize(shape, interpolation))


def ptpscale(img):
    a, b = min(img.flat), max(img.flat)
    if a == b:
        return np.zeros_like(img)
    return (img - a) * 255 / (b - a)


class ImageDirOut(object):
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
        imsave(img, os.path.join(self.dirname, '%.8d.%s' % (self.fcnt, self.format)), self.format)
        self.fcnt += 1

    def viewsc(self, img):
        self.view(ptpscale(img))




