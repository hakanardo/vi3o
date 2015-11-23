from cffi import FFI

ffi = FFI()
ffi.cdef("""
        struct mkv {
            int width, height;
            char mac[13];
            int64_t systime_offset_sum, systime_offset_count, systime_offset;
            uint8_t *codec_private;
            size_t codec_private_len;
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
        void mkv_estimate_systime_offset(struct mkv *s);

        struct decode;
        struct decode *decode_open(struct mkv *m);
        int decode_frame(struct decode *p, struct mkv_frame *frm, uint8_t *img, uint64_t *ts);

         """)
ffi.set_source("_mkv", '#include "decode.h"', sources=["mkv.c", "decode.c"],
               libraries=["avcodec", "swscale"])
ffi.compile()
