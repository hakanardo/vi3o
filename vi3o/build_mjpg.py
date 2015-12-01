from cffi import FFI

ffi = FFI()
ffi.cdef("""
        struct mjpg {
            int width, height;
            unsigned char *pixels;
            unsigned int timestamp_sec;
            unsigned int timestamp_usec;
            long start_position_in_file, stop_position_in_file;
            ...;
        };
        enum {OK, ERROR_FILENOTFOUND, ERROR_ILLEGALARGUMENT, ERROR_FILEFORMAT,
              ERROR_EOF, ERROR_FAIL};
        enum {IMORDER_PLANAR, IMORDER_PLANAR_SUBX, IMORDER_PLANAR_SUBXY,
              IMORDER_INTERLEAVED};
        enum {IMTYPE_GRAY, IMTYPE_YCbCr, IMTYPE_RGB, IMTYPE_BGR};

        int mjpg_open(struct mjpg *m, char *name, int type, int dataOrder);
        int mjpg_next_head(struct mjpg *m);
        int mjpg_next_data(struct mjpg *m);
        int mjpg_close(struct mjpg *m);
        int mjpg_seek (struct mjpg *m, long offset);
         """)
ffi.set_source("_mjpg", '#include "mjpg.h"', sources=["mjpg.c"], libraries=["jpeg"])
ffi.compile()
