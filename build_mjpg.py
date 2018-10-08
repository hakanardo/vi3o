from cffi import FFI
import os

mydir = os.path.abspath(os.path.dirname(__file__))

ffi = FFI()
ffi.cdef("""
        struct mjpg {
            int width, height;
            unsigned char *pixels;
            unsigned int timestamp_sec;
            unsigned int timestamp_usec;
            long start_position_in_file, stop_position_in_file;
            char hwid[32];
            char serial[32];
            char firmware[32];
            ...;
        };
        enum {OK, ERROR_FILENOTFOUND, ERROR_ILLEGALARGUMENT, ERROR_FILEFORMAT,
              ERROR_EOF, ERROR_FAIL};
        enum {IMORDER_PLANAR, IMORDER_PLANAR_SUBX, IMORDER_PLANAR_SUBXY,
              IMORDER_INTERLEAVED};
        enum {IMTYPE_GRAY, IMTYPE_YCbCr, IMTYPE_RGB, IMTYPE_BGR};

        int mjpg_open(struct mjpg *m, char *name, int type, int dataOrder);
        int mjpg_open_buffer(struct mjpg *m, uint8_t *buf, int len, int type, int dataOrder);
        int mjpg_next_head(struct mjpg *m);
        int mjpg_next_data(struct mjpg *m);
        int mjpg_close(struct mjpg *m);
        int mjpg_seek (struct mjpg *m, long offset);

         """)
ffi.set_source("vi3o._mjpg", '#include "src/mjpg.h"',
               include_dirs=[mydir],
               sources=["src/mjpg.c"],
               libraries=["jpeg"], )

if __name__ == '__main__':
    ffi.compile()

