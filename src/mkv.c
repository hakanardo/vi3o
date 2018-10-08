#include <assert.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <sys/mman.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "mkv.h"

static uint64_t get_id(struct mkv *s) {
    int i;
    uint64_t id = 0;
    if (s->cur >= s->data + s->len || !s->cur[0]) {
        s->cur++;
        return 0;
    }
    for (i=0; (s->cur[0] >> (8-i)) != 1; i++) {
        if (s->cur + i >= s->data + s->len) {
            s->cur += i;
            return 0;
        }
        id = (id << 8) + s->cur[i];
    }
    s->cur += i;
    return id;
}


static uint64_t get_size(struct mkv *s) {
    uint64_t len = get_id(s);
    uint64_t msk = 1;
    while (len > msk) msk <<= 1;
    msk >>= 1;
    return len & (~msk);
}

static uint64_t get_uint(struct mkv *s, int len) {
    uint64_t val = 0;
    while (len--) val = (val << 8) | *s->cur++;
    return val;
}

struct mkv *mkv_open(char *filename) {
    struct mkv *s = calloc(sizeof(struct mkv), 1);
    int fd = open(filename, O_RDONLY);
    assert(fd>0);
    struct stat st;
    fstat(fd, &st);
    s->len = st.st_size;
    s->data = s->cur = mmap(NULL, s->len, PROT_READ, MAP_SHARED, fd, 0);
    assert(s->data != MAP_FAILED);
    close(fd);
    s->munmap_on_close = 1;
    s->codec_private = NULL;
    s->codec_private_len = 0;
    s->codec_id = NULL;
    return s;
}

void mkv_close(struct mkv *s) {
    if (s->munmap_on_close) {
        munmap(s->data, s->len);
    }
    if (s->codec_id) free(s->codec_id);
    free(s);
}

int handle_axis_block(struct mkv *s, uint8_t *data, int len, uint64_t ts) {
    uint8_t hdr[] = {0x06, 0x05};
    uint8_t uid[] = {0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa,
                     0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa};
    uint8_t prd[] = {0x00, 0x0d, 0x0a, 0x00};
    uint8_t tim[] = {0x00, 0x0d, 0x0a, 0x01};

    assert(len > 4 + sizeof(hdr) + 1);
    data += 4;
    len -= 4;

    int pos = 0;
    if (!memcmp(data, hdr, sizeof(hdr))) {
        pos += sizeof(hdr) + 1;
        while (pos + sizeof(uid) < len) {
            if (!memcmp(data + pos, uid, sizeof(uid))) {
                pos += sizeof(uid);
                if (!memcmp(data + pos, prd, sizeof(prd))) {
                    pos += sizeof(prd);
                    sprintf(s->mac, "%2X%2X%2X%2X%2X%2X", data[pos+5], data[pos+6],
                            data[pos+7], data[pos+8], data[pos+9], data[pos+10]);
                    pos += 11;
                }
            } if (!memcmp(data + pos, tim, sizeof(tim))) {
                pos += sizeof(tim);
                int64_t systime = (data[pos+0]<<24) +
                                  (data[pos+1]<<16) +
                                  (data[pos+2]<<8) +
                                  (data[pos+3]<<0);
                systime *= 1000000;
                systime += data[pos+4] * 10000;
                s->systime_offset_sum += systime-ts;
                s->systime_offset_count += 1;
                return 1;
            } else {
                break;
            }
        }
    }
    return 0;
}

int mkv_next(struct mkv *s, struct mkv_frame *frm) {
    while (s->cur < s->data + s->len) {
        unsigned long offset = s->cur - s->data;
        uint64_t id = get_id(s);
        uint64_t len = get_size(s);
        switch(id) {
            case 0x18538067: // Segment
            break;
            case 0x1549A966: // Segment Information
            break;
            case 0x2AD7B1: // TimecodeScale
                if (s->cur + len > s->data + s->len) {s->cur += len; break;}
                s->time_scale = get_uint(s, len);
                break;
            case 0x1f43b675: // Cluster
                s->cluster_offset = offset;
                break;
            case 0xE7: // Timecode
                if (s->cur + len > s->data + s->len) {s->cur += len; break;}
                s->time_offset = get_uint(s, len);
                break;
            case 0xa3: // SimpleBlock
                if (s->cur + len > s->data + s->len) {s->cur += len; break;}
                assert(s->cur[0] == 129);
                frm->pts = s->time_offset + (s->cur[1]<<8) + s->cur[2];
                frm->pts *= s->time_scale / 1000;
                if (s->systime_offset) {
                    frm->systime = frm->pts + s->systime_offset;
                } else {
                    frm->systime = 0;
                }
                frm->data = s->cur + 4;
                frm->offset = s->cluster_offset;
                frm->len = len - 4;
                frm->key_frame = (s->cur[3]&0x80)>>7;
                s->cur += len;
                if (!handle_axis_block(s, frm->data, frm->len, frm->pts)) {
                    return 1;
                }
                break;
            case 0xa4: // CodecState
                assert(0); // Not implemented
                break;
            case 0x1654ae6b: // Tracks
                break;
            case 0xae: // TrackEntry
                break;
            case 0x63a2: // CodecPrivate
                if (s->cur + len > s->data + s->len) {s->cur += len; break;}
                s->codec_private = s->cur;
                s->codec_private_len = len;
                s->cur += len;
                break;
            case 0x86: // CodecId
                s->codec_id = strndup(s->cur, len);
                s->cur += len;
                break;
            case 0xE0: // Video
                break;
            case 0xb0: // PixelWidth
                if (s->cur + len > s->data + s->len) {s->cur += len; break;}
                s->width = get_uint(s, len);
                break;
            case 0xba: // PixelHeight
                if (s->cur + len > s->data + s->len) {s->cur += len; break;}
                s->height = get_uint(s, len);
                break;
            default:
                //printf("0x%x\n", id);
                s->cur += len;
        }
    }
    memset(frm, 0, sizeof(struct mkv_frame));
    return 0;
}

void mkv_seek(struct mkv *s, unsigned long offset) {
    assert(offset < s->len);
    s->cur = s->data + offset;

}

int64_t mkv_estimate_systime_offset(struct mkv *s) {
    uint8_t *org = s->cur;
    struct mkv_frame frm;
    while (mkv_next(s, &frm));
    if (s->systime_offset_count == 0) return 0;
    s->systime_offset = s->systime_offset_sum / s->systime_offset_count;
    s->cur = org;
    return s->systime_offset;
}
