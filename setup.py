from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys
import os

# Read the version but avoid importing the __init__.py since
# we might not have all dependencies installed
with open(os.path.join(os.path.dirname(__file__), "vi3o", "version.py")) as fp:
    exec(fp.read())

PY3_3 = sys.version_info <= (3,3,0)
PY2 = sys.version_info <= (2, 8, 0)

def _resolve_numpy():
    if PY2:
        return "numpy >= 1.7.1, < 1.17"
    return "numpy >= 1.7.1"

constraints = {
        "mock": "mock <= 3.0.5",
        "cffi": "cffi>=1.0.0",
        "pathlib": "pathlib2" if PY3_3 else "pathlib",
        "numpy": _resolve_numpy(),
        "pillow": "pillow < 7" if PY2 else "pillow",
        "pyglet": "pyglet < 1.5" if PY2 else "pyglet",
        "pytest": "pytest <= 4.6, !=4.6.0",

}

_test_keys = ["pytest", "pillow"]
if PY2:
    _test_keys.append("mock")

requirements_full = [constraints[key] for key in ["pyglet", "pillow"]]
requirements_test = [constraints[key] for key in _test_keys]
requirements = [constraints[key] for key in ["cffi", "numpy"]]

class PyTestCommand(TestCommand):
    user_options = []

    def finalize_options(self):
        pass

    def run_tests(self):
        import pytest
        errno = pytest.main()
        sys.exit(errno)

setup(
    name='vi3o',
    description='VIdeo and Image IO',
    long_description='''
Utility for loading/saving/displaying video and images. It gives random
access to mjpg (in http multipart format) and H264 (in .mkv format) video
frames. For recordings origination from Axis cameras the camera system
time at the time of capture is provided as timestamp for each frame.
    ''',
    version=__version__,
    packages=['vi3o'],
    zip_safe=False,
    url='http://vi3o.readthedocs.org',
    author='Hakan Ardo',
    author_email='hakan@debian.org',
    license='MIT',
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=["build_mjpg.py:ffi", "build_mkv.py:ffi"],
    install_requires=requirements,
    extras_require={
        "full": requirements_full
    },
    cmdclass={'test': PyTestCommand},
    tests_require=requirements_test,
)
