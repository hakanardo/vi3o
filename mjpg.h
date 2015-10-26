#ifndef MJPG_H_KJGFHDHCNB
#define MJPG_H_KJGFHDHCNB

#include <stdio.h>
#include <jpeglib.h>
#include <setjmp.h>

#define CM_OK                    0
#define CM_FAIL                  1

enum {OK=0, ERROR_FILENOTFOUND, ERROR_ILLEGALARGUMENT, ERROR_FILEFORMAT,
      ERROR_EOF, ERROR_FAIL};
enum {IMORDER_PLANAR, IMORDER_PLANAR_SUBX, IMORDER_PLANAR_SUBXY,
      IMORDER_INTERLEAVED};
enum {IMTYPE_GRAY, IMTYPE_YCbCr, IMTYPE_RGB, IMTYPE_BGR};

#define MAX_SEPARATOR_LEN 100

struct my_error_mgr {
  struct jpeg_error_mgr pub;    /* "public" fields */
  jmp_buf setjmp_buffer;        /* for return to caller */
};

struct mjpg {
  struct jpeg_decompress_struct cameraDecomp;
  JSAMPARRAY cameraBuffer[3];            /* Output row buffer */
  struct my_error_mgr cameraJerr;
  int type;
  FILE *fd;
  
  char mjpg_separator[MAX_SEPARATOR_LEN];
  int width, height, dataOrder;
  char *pixels;

  int nErr;

  unsigned int timestamp_sec;   /**< Timestamp in seconds when this frame were exposed */
  unsigned int timestamp_usec;  /**< Microseconds to add to timestamp_sec for higher precition */
  long start_position_in_file, stop_position_in_file;
};

int mjpg_open(struct mjpg *m, char *name, int type, int dataOrder);
int mjpg_next(struct mjpg *m);
int mjpg_close(struct mjpg *m);

int mjpg_seek (struct mjpg *m, long offset, int whence);

int mjpg_open_fd(struct mjpg *m, FILE *fd, int type, int dataOrder);
int mjpg_close_fd(struct mjpg *m);

#endif