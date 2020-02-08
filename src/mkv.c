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


/*
 * General flow to read elements:
 * ------------------------------
 * If mkv container is read from start of file we set the following properties
 * from the information in the Section->Track->TrackEntries element that we do
 * not expect to change:
 * 
 * codec_private
 * codec_private_len
 * width
 * height
 * codec_id
 *
 * When reading through the data to find the frames we will update these fields
 * for each cluster:
 *
 * time_scale
 * time_offset
 * cluster_offset
 * 
 *
 * Estimate axis-specific time stamps:
 * -----------------------------------
 * If the data blocks have expected markers for an Axis camera we will also
 * parse the camera MAC-address and the camera system time for each frame.
 *
 * Since we base the camera system time on the everage offset we first need to
 * parse all (or some) frames to get the sum of the offsets, then call the
 * mkv_estimate_systime_offset() function. After this all frames that we read will
 * get the systime variable set to the sum of the offset and frame time. Otherwise
 * this will be 0.
 *
 * --------------------------------------------------------
 * For some summerized information on matroska format, see:
 * https://www.matroska.org/files/matroska.pdf
 */


/*
 * Read the element ID staring at the cursor position and
 * advance the cursor to the next byte after the ID. The
 * ID is returned including the leading 1 (which is
 * guaranteed since the UTF-like encoding)
 */
static uint64_t get_id(struct mkv *s) {
    int i;
    uint64_t id = 0;
    /* Sanity check, within mmaped bounds and leading
    /  byte should always containt atleast one set bit
    /  due to the UTF-like format */
    if (s->cur >= s->data + s->len || !s->cur[0]) {
        s->cur++;
        return 0;
    }
    /* Read one byte for each leading zero and the
    /  flowing one in the first byte. The loop will
    /  always run atleast once since right shifting
    /  a 1 byte value 8 bits always is 0. */
    for (i=0; (s->cur[0] >> (8-i)) != 1; i++) {
        /* Make sure were not out of mmaped area... */
        if (s->cur + i >= s->data + s->len) {
            s->cur += i;
            return 0;
        }
        /* Read the id-byte... */
        id = (id << 8) + s->cur[i];
    }
    /* Move cursor to point on first byte after ID */
    s->cur += i;
    return id;
}

/*
 * Read the size of an element, expects cursor to be at
 * first byte of the size data.
 */
static uint64_t get_size(struct mkv *s) {
    /* Size has same UTF-like format as ID, so use that function.. */
    uint64_t len = get_id(s);
    /* Remove the leading 1 in the upper byte to get the payload */
    uint64_t msk = 1;
    while (len > msk) msk <<= 1;
    msk >>= 1;
    return len & (~msk);
}

/*
 * Read <len> bytes starting at cursor and interpret as unsigned int
 */
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

/*
 * Try to parse the Axis camera specific data from the data bytes in
 * a SimpleBlock.
 */
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
            }
            if (!memcmp(data + pos, tim, sizeof(tim))) {
                pos += sizeof(tim);
                // Read the systime at this frame
                // (with 1/100:th of a second in resolution)
                int64_t systime = (data[pos+0]<<24) +
                                  (data[pos+1]<<16) +
                                  (data[pos+2]<<8) +
                                  (data[pos+3]<<0);
                systime *= 1000000;
                systime += data[pos+4] * 10000;
                // Since the SimpleBlock timecode has better resoluution
                // we accumulate the system time offset from the frame
                // timestamps and uses that to get higher resolution
                // on the system time
                s->systime_offset_sum += systime-ts;
                s->systime_offset_count += 1;
                // Verify expected position of markers
                if (len - pos > 12) {
                    // All good!
                    return 0;
                }
                return 1;  // Bad data?
            } else {
                break;
            }
        }
    }
    return 0;
}

/*
 * Read the content of a SimpleBlock in a video cluster
 * Expected format:
 *
 * vint TrackNumber
 * sint16 Timecode (relative to cluster timecode)
 * int8 Flags (lacing=False, keyframe, invisible, discardable)
 * int8 [] data
 */
int read_simple_block(struct mkv *s, struct mkv_frame *frm, uint64_t len) {
    // Track number 1 expected (as variable length int)
    assert(s->cur[0] == 129);
    // Calculate system time from the timecode
    // timecode in bigendian
    //int16_t timecode = (int16_t) (((uint16_t)s->cur[1]<<8) + s->cur[2]);
    int16_t timecode = (int16_t) ((s->cur[1]<<8) + s->cur[2]);
    // Add the cluster timecode offset
    frm->pts = s->time_offset + timecode;
    // Multiply with the TimecodeScale to get time in nanoseconds, divide
    // to get time in microseconds
    frm->pts *= s->time_scale / 1000;
    // Axis camera specific systime offset
    if (s->systime_offset) {
        frm->systime = frm->pts + s->systime_offset;
    } else {
        frm->systime = 0;  // No info about system time
    }
    // Set data pointers for frame to use rest of the data
    frm->data = s->cur + 4;
    frm->offset = s->cluster_offset;
    frm->len = len - 4;
    frm->key_frame = (s->cur[3]&0x80)>>7;
    // Advance cursor to next element
    s->cur += len;

    // Try to parse axis specific data
    return handle_axis_block(s, frm->data, frm->len, frm->pts);
}

int mkv_next(struct mkv *s, struct mkv_frame *frm) {
    while (s->cur < s->data + s->len) {
        unsigned long offset = s->cur - s->data; /* Bytes from start of file */
        uint64_t id = get_id(s); /* Read element ID and advance cursor position */
        uint64_t len = get_size(s); /* Read element size and advance cursor */
        switch(id) {
            case 0x18538067: // Segments
                break;
            case 0x1549A966: // Segments->Segment Information
                break;
            case 0x2AD7B1: // Segments->Segment Information->TimecodeScale
                // All scaled timecodes should be multiplied with this number
                // to get the time in nanoseconds
                if (s->cur + len > s->data + s->len) {s->cur += len; break;}
                s->time_scale = get_uint(s, len);
                break;
            case 0x1f43b675: // Segments->Cluster
                // A cluster contains multimedia data and usually spans over
                // a range of a few seconds
                s->cluster_offset = offset;
                break;
            case 0xE7: // Segments->Cluster->Timecode
                // The Cluster timecode is the timecode all block timecodes are
                // indicated relatively to
                if (s->cur + len > s->data + s->len) {s->cur += len; break;}
                s->time_offset = get_uint(s, len);
                break;
            case 0xa3: // Segments->Cluster->SimpleBlock
                if (s->cur + len > s->data + s->len) {s->cur += len; break;}
                if (!read_simple_block(s, frm, len)) {
                    return 1;
                }
                break;
            case 0xa4: // CodecState
                assert(0); // Not implemented
                break;
            case 0x1654ae6b: // Segments->Tracks
                break;
            case 0xae: // Segments->Tracks->TrackEntry
                break;
            case 0xd7: // Segments->Tracks->TrackEntry->TrackNumber
                if (s->cur + len > s->data + s->len) {s->cur += len; break;}
                uint64_t track_number = get_uint(s, len);
                break;
            case 0x83: // Segments->Tracks->TrackEntry->TrackType
                // defines the type of a track, i.e. video, audio, subtitle etc.
                // 0x01 video track
                // 0x03 complex track, e.g. audio + video
                // 0x02, 0x10, 0x11, 0x12, 0x20 Other...
                if (s->cur + len > s->data + s->len) {s->cur += len; break;}
                uint64_t track_type = get_uint(s, len);
                break;
            case 0x63a2: // Segments->Tracks->TrackEntry->CodecPrivate
                // Information Codec needs before decoding can start 
                if (s->cur + len > s->data + s->len) {s->cur += len; break;}
                s->codec_private = s->cur;
                s->codec_private_len = len;
                s->cur += len;
                break;
            case 0x86: // Segments->Tracks->TrackEntry->CodecId
                // Specifies the Codec which is used to decode the track
                s->codec_id = strndup((char *)s->cur, len);
                s->cur += len;
                break;
            case 0xE0: // Segments->Tracks->TrackEntry->Video
                // Contains information that is specific for video tracks
                break;
            case 0xb0: // Segments->Tracks->TrackEntry->Video->PixelWidth
                if (s->cur + len > s->data + s->len) {s->cur += len; break;}
                s->width = get_uint(s, len);
                break;
            case 0xba: // Segments->Tracks->TrackEntry->Video->PixelHeight
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
