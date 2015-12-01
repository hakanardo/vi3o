import tempfile
import shutil
from contextlib import contextmanager

@contextmanager
def TempDir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)
