from cffi import FFI
import os

mydir = os.path.abspath(os.path.dirname(__file__))

ffi = FFI()
ffi.cdef("""
        struct mkv {
            int width, height;
            char mac[13];
            int64_t systime_offset_sum, systime_offset_count, systime_offset;
            uint8_t *codec_private;
            size_t codec_private_len;
            char *codec_id;
            ...;
        };
        struct mkv_frame {
            uint64_t pts, systime;
            uint8_t *data;
            unsigned long len;
            unsigned long offset;
            int key_frame;
        };

        struct mkv *mkv_open(char *filename);
        void mkv_close(struct mkv *s);
        int mkv_next(struct mkv *s, struct mkv_frame *frm);
        void mkv_seek(struct mkv *s, unsigned long offset);

        struct decode;
        struct decode *decode_open(struct mkv *m);
        void decode_close(struct decode *p);
        int decode_frame(struct decode *p, struct mkv_frame *frm, uint8_t *img, uint64_t *ts, int grey);
        int64_t mkv_estimate_systime_offset(struct mkv *s);

         """)
ffi.set_source("vi3o._mkv", '#include "decode.h"',
               include_dirs=[mydir],
               sources=[os.path.join(mydir, "mkv.c"), os.path.join(mydir,"decode.c")],
               # cflags=["-g"],
               libraries=["avcodec", "swscale"])

if __name__ == '__main__':
    ffi.compile()
