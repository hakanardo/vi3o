import PIL.Image
import numpy as np

NEAREST = PIL.Image.NEAREST
BILINEAR = PIL.Image.BILINEAR
BICUBIC = PIL.Image.BICUBIC
ANTIALIAS = PIL.Image.ANTIALIAS


def imsave(img, filename, format=None):
    if format is None:
        format = filename.split('.')[-1]
    if format == 'jpg':
        format = 'jpeg'
    PIL.Image.fromarray(img).save(filename, format.lower())


def imread(filename):
    return np.array(PIL.Image.open(filename))


def imscale(img, shape, interpolation=NEAREST):
    if isinstance(shape, float) or isinstance(shape, int):
        shape = (shape * img.shape[1], shape * img.shape[0])
    shape = map(int, shape)
    return np.array(PIL.Image.fromarray(img).resize(shape, interpolation))


