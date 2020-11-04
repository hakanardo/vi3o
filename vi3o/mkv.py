import json
import os
from vi3o.utils import SlicedView, index_file, Frame
try:
    from vi3o._mkv import ffi, lib
    from vi3o._mjpg import lib as mjpg_lib
    from vi3o._mjpg import ffi as mjpg_ffi
except ImportError as e:
    import warnings
    warnings.warn("Failed to import. Try to recompile/reinstall vi3o. " + str(e))


from threading import Lock
decode_open_lock = Lock()

INDEX_VERSION = 4

class Mkv(object):
    def __init__(self, filename, grey=False, reindex=False):
        # Be compatible with pathlib.Path filenames
        filename = str(filename).encode('utf-8')
        self.filename = filename
        self.grey = grey
        open(filename).close()
        self._myiter = None
        self.systime_offset = 0

        need_index = True
        idx = index_file(self.filename)
        if os.path.exists(idx):
            try:
                index = json.load(open(idx))
            except Exception:
                pass
            else:
                if index['version'] == INDEX_VERSION:
                    self.frame = index['frame']
                    self.systime_offset = index['systime_offset']
                    self.mjpg_mode = index['mjpg_mode']
                    need_index = False

        if need_index or reindex:
            self.frame = []
            m = lib.mkv_open(self.filename)
            frm = ffi.new('struct mkv_frame *')
            cluster_offsets = set()
            while lib.mkv_next(m, frm):
                if frm.key_frame:
                    if frm.offset in cluster_offsets:
                        print("FIXME: Multiple keyframes per cluster!")
                    cluster_offsets.add(frm.key_frame)
                self.frame.append([frm.pts, frm.offset, frm.key_frame])
            self.frame.sort()
            self.systime_offset = iter(self).estimate_systime_offset() # FIXME: This makes a second pass over the file parsing it
            self.mjpg_mode = (ffi.string(m.codec_id) == b'V_MS/VFW/FOURCC')
            lib.mkv_close(m)

            tmp = idx + '.tmp.%d' % os.getpid()
            with open(tmp, 'w') as fd:
                json.dump({'frame': self.frame,
                           'systime_offset': self.systime_offset,
                           'mjpg_mode': self.mjpg_mode,
                           'version': INDEX_VERSION}, fd)
            try:
                os.link(tmp, idx)
            except FileExistsError:
                pass
            os.unlink(tmp)

    @property
    def systimes(self):
        if self.mjpg_mode:
            raise NotImplementedError
        return [float(f[0] + self.systime_offset) / 1000000.0 for f in self.frame]

    def _sliced_systimes(self, range):
        return [self.systimes[i] for i in range]

    @property
    def serial_number(self):
        """
        The Axis serial number or mac address of the camera that made this recording.
        """
        self.myiter.next()
        return ffi.string(self.myiter.m.mac)

    def __iter__(self):
        return MkvIter(self.filename, self.systime_offset, self.grey)

    @property
    def myiter(self):
        if self._myiter is None:
            self._myiter = iter(self)
        return self._myiter

    def __getitem__(self, item):
        if isinstance(item, slice):
            return SlicedView(self, item, {'systimes': self._sliced_systimes})
        if (item < 0):
            item += len(self)
        keyindex = item
        while self.frame[keyindex][2] == 0:
            keyindex -= 1
            assert keyindex >= 0
        pts = self.frame[item][0]
        if keyindex > self.myiter.fcnt or item < self.myiter.fcnt:
            lib.mkv_seek(self.myiter.m, self.frame[keyindex][1])
            lib.mkv_next(self.myiter.m, self.myiter.frm)
        for img in self.myiter:
            if img.pts == pts or self.mjpg_mode:
                img.index = item
                self.myiter.fcnt = item + 1
                return img
            elif img.pts > pts:
                pass # We might get newer frames that was already in the pipe before the seek
        assert False

    def __len__(self):
        return len(self.frame)

    def __getstate__(self):
        state = dict(self.__dict__)
        del state['_myiter']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._myiter = None


class DecodeError(Exception):
    pass

class H264Decoder(object):
    def open(self, m):
        with decode_open_lock:
            self.p = lib.decode_open(m)

    def __del__(self):
        with decode_open_lock:
            self.p = lib.decode_close(self.p)

    def decode_frame(self, frm, pixels, pts, grey):
        return lib.decode_frame(self.p, frm, pixels, pts, grey)

class MjpgDecoder(object):
    def open(self, m):
        pass

    def decode_frame(self, frm, pixels, pts, grey):
        if frm.len == 0:
            return 0
        m = mjpg_ffi.new("struct mjpg *")
        if grey:
            r = mjpg_lib.mjpg_open_buffer(m, frm.data, frm.len, mjpg_lib.IMTYPE_GRAY, mjpg_lib.IMORDER_INTERLEAVED)
        else:
            r = mjpg_lib.mjpg_open_buffer(m, frm.data, frm.len, mjpg_lib.IMTYPE_RGB, mjpg_lib.IMORDER_INTERLEAVED)
        if r != mjpg_lib.OK:
            raise IOError("Failed to decode frame")

        if mjpg_lib.mjpg_next_head(m) != mjpg_lib.OK:
            return 0
        m.pixels = mjpg_ffi.cast('unsigned char *', pixels)
        if mjpg_lib.mjpg_next_data(m) != mjpg_lib.OK:
            return 0
        pts[0] = m.timestamp_sec * 1000000 + m.timestamp_usec
        mjpg_lib.mjpg_close(m)

        return 1

class MkvIter(object):
    def __init__(self, filename, systime_offset, grey=False):
        self.m = lib.mkv_open(filename)
        self.systime_offset = systime_offset
        self.frm = ffi.new('struct mkv_frame *')
        self.out_of_packages = False
        lib.mkv_next(self.m, self.frm)
        assert self.m.codec_private
        assert self.m.codec_private_len > 0
        if ffi.string(self.m.codec_id) == b'V_MS/VFW/FOURCC':
            self.decoder = MjpgDecoder()
        else:
            self.decoder = H264Decoder()

        self.decoder.open(self.m)
        self.fcnt = 0
        self.pts = ffi.new('uint64_t *')
        if grey:
            self.channels = 1
        else:
            self.channels = 3
        if not self.m:
            raise IOError("Failed to open: " + filename)

    def __del__(self):
        del self.decoder
        lib.mkv_close(self.m)

    def estimate_systime_offset(self):
        return lib.mkv_estimate_systime_offset(self.m)

    def __iter__(self):
        return self

    def next(self):
        assert self.m.width > 0
        if self.channels == 1:
            shape = (self.m.height, self.m.width)
        else:
            shape = (self.m.height, self.m.width, self.channels)

        img = Frame(shape, 'B')
        assert img.__array_interface__['strides'] is None
        pixels = ffi.cast('uint8_t *', img.__array_interface__['data'][0])

        while True:
            r = self.decoder.decode_frame(self.frm, pixels, self.pts, self.channels == 1)
            if r >= 0:
                if lib.mkv_next(self.m, self.frm) == 0 and r == 0:
                    raise StopIteration
                if r == 1:
                    break
            else:
                raise DecodeError

        img.index = self.fcnt
        img.pts = self.pts[0]
        img.timestamp = float(img.pts) / 1000000.0
        img.systime = float(img.pts + self.systime_offset) / 1000000.0
        self.fcnt += 1
        return img

    def __next__(self):
        return self.next()

    def __getstate__(self):
        raise NotImplementedError("Cant pickle MkvIter objects")


class MkvStream(object):
    def __init__(self, data):
        self.data = data
