#ifndef __MKV__H__
#define __MKV__H__

#include <stdint.h>

struct mkv;
struct mkv_frame {
    uint64_t pts;  // Frame time from the matroska SimpleBlock
    uint64_t systime;  // Systime if has axis specific block
    uint8_t *data;  // Data pointer to frame data
    unsigned long len;  // Length of frame data
    unsigned long offset;  // Offset for current cluster
    int key_frame;  // Set if this is a key-frame, else 0
};

struct mkv {
    uint8_t *cur;  // Current cursor position
    uint8_t *data; // Start address of mapped data
    size_t len; // Total size of mapped video in bytes
    int munmap_on_close;
    long time_scale;  // Current segment time multiplier to get nano sec
    long time_offset;  // Current segement time offset (scaled)
    uint8_t *codec_private;  // Extra info to decoder
    size_t codec_private_len;
    int width, height;  // Image width and height
    char mac[13];  // Camera MAC if axis data block
    int64_t systime_offset_sum;  // Sum of axis systimes offsets from frame time for all frames
    int64_t systime_offset_count;  // Number of summed frames
    int64_t systime_offset;  // Average systime offset from frame time
    unsigned long cluster_offset;  // Current cluster element start as bytes from data
    char *codec_id;  // Codec identifier
};

/*
 * Open an MKV video file
 */
struct mkv *mkv_open(char *filename);

/*
 * Close the video file
 */
void mkv_close(struct mkv *s);

/*
 * Find the next frame from current cursor
 */
int mkv_next(struct mkv *s, struct mkv_frame *frm);

/*
 * Move cursor to offset in bytes
 */
void mkv_seek(struct mkv *s, unsigned long offset);

/*
 * Estimate the system time offset if the video is from an Axis camera.
 * The time is estimated as an average offset from the frame time (pts)
 * since the frame time is in nanosecond resolution and the systemtime
 * for a block has a resolution of 10 milli seconds. Average offset is
 * estimated on all frames after the current cursor position.
 *
 * Current cursor position is restored after the call.
 */
int64_t mkv_estimate_systime_offset(struct mkv *s);

#endif
