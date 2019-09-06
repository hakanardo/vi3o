from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys
import os

is_PY2 = sys.version_info <= (3, 0, 0)

KEYWORDS = [
    "video", "mkv", "mjpg"
]

CLASSIFIERS = [
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT",
    "Natural Language :: English",
    "Operating System :: Linux",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python",
    "Topic :: Software Development :: Libraries :: Python Modules"
]

INSTALL_REQUIRES = ["cffi>=1.0.0", "numpy>=1.7.1,<1.17"]
if is_PY2:
    INSTALL_REQUIRES.append("pathlib2")

SETUP_REQUIRES = [
    'cffi>=1.0.0'
]

EXTRAS_REQUIRE = {
    "dev": [
        "coverage",
        "pytest <= 4.6, != 4.6.0",
        "pillow < 7",
        "sphinx < 1.8",
    ],
    "full": [
        "pillow < 7",
        "pyglet < 1.5"
    ]
}

if is_PY2:
    EXTRAS_REQUIRE['dev'].append('mock')


PACKAGES = find_packages(where="src")

CFFI_MODULES = [
    "src/_cffi_src/build_mjpg.py:ffi", 
    "src/_cffi_src/build_mkv.py:ffi"
]

# Read the version but avoid importing the __init__.py since
# we might not have all dependencies installed
with open(os.path.join(os.path.dirname(__file__), "src", "vi3o", "version.py")) as fp:
    exec(fp.read())

setup(
    name='vi3o',
    description='VIdeo and Image IO',
    license='MIT',
    url='http://vi3o.readthedocs.org',
    author='Hakan Ardo',
    author_email='hakan@debian.org',
    long_description='''
Utility for loading/saving/displaying video and images. It gives random
access to mjpg (in http multipart format) and H264 (in .mkv format) video
frames. For recordings origination from Axis cameras the camera system
time at the time of capture is provided as timestamp for each frame.
    ''',
    version=__version__,
    keywords=KEYWORDS,
    classifiers=CLASSIFIERS,
    packages=PACKAGES,
    package_dir={"": "src"},
    setup_requires=SETUP_REQUIRES,
    cffi_modules=CFFI_MODULES,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    zip_safe=False,
)
