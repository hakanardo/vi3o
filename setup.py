from setuptools import setup, Command
from vi3o import __version__
import sys

class PyTestCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
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
    install_requires=["cffi>=1.0.0"],
    cmdclass={'test': PyTestCommand},
    tests_require=['pytest'],
)
