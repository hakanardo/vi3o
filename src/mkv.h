#ifndef __MKV__H__
#define __MKV__H__

#include <stdint.h>

struct mkv;
struct mkv_frame {
    uint64_t pts, systime;
    uint8_t *data;
    unsigned long len;
    unsigned long offset;
    int key_frame;
};

struct mkv {
    uint8_t *cur;
    uint8_t *data;
    size_t len;
    int munmap_on_close;
    long time_scale;
    long time_offset;
    uint8_t *codec_private;
    size_t codec_private_len;
    int width, height;
    char mac[13];
    int64_t systime_offset_sum, systime_offset_count, systime_offset;
};

struct mkv *mkv_open(char *filename);
void mkv_close(struct mkv *s);
int mkv_next(struct mkv *s, struct mkv_frame *frm);
void mkv_seek(struct mkv *s, unsigned long offset);
int64_t mkv_estimate_systime_offset(struct mkv *s);

#endif
