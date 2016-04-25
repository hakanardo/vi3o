#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <time.h>

#include <libavcodec/avcodec.h>
#include <libavutil/avutil.h>
#include <libswscale/swscale.h>

#include "decode.h"

#if (LIBAVCODEC_VERSION_MAJOR < 55)
#define AV_CODEC_ID_H264 CODEC_ID_H264
#endif

#if (LIBAVUTIL_VERSION_MAJOR < 55)
#define AV_PIX_FMT_RGB24 PIX_FMT_RGB24
#define AV_PIX_FMT_GRAY8 PIX_FMT_GRAY8
#endif

struct decode {
    AVCodec* codec;                                                                        /* the AVCodec* which represents the H264 decoder */
    AVCodecContext* codec_context;                                                         /* the context; keeps generic state */
    AVFrame* picture;                                                                      /* will contain a decoded picture */
    uint64_t next_time;
    struct mkv *m;
};

struct decode *decode_open(struct mkv *m) {

    assert(m);
    assert(m->codec_private);

    struct decode *p = calloc(sizeof(struct decode), 1);
    p->next_time = 0;
    p->m = m;

    static int avcodec_register_all_called=0;
    if (!avcodec_register_all_called) {
        avcodec_register_all();
        avcodec_register_all_called = 1;
    }

    p->codec = avcodec_find_decoder(AV_CODEC_ID_H264);
    assert(p->codec);
    p->codec_context = avcodec_alloc_context3(p->codec);
    assert(p->codec_context);
    p->codec_context->extradata = m->codec_private;
    p->codec_context->extradata_size = m->codec_private_len;
    int rc = avcodec_open2(p->codec_context, p->codec, NULL);
    assert(rc>=0);
    //p->picture = av_frame_alloc();
    p->picture = avcodec_alloc_frame();

    return p;
}

void decode_close(struct decode *p) {
    av_free(p->picture);
    p->picture = NULL;
    avcodec_close(p->codec_context);
    av_free(p->codec_context);
    p->codec_context = NULL;
}

int decode_frame(struct decode *p, struct mkv_frame *frm, uint8_t *img, uint64_t *ts, int grey) {
    AVPacket pkt;
    av_init_packet(&pkt);
    pkt.data = frm->data;
    pkt.size = frm->len;
    pkt.pts = frm->pts;
    int got_picture = 0;
    int len = avcodec_decode_video2(p->codec_context, p->picture,
                                    &got_picture, &pkt);
    if (len < 0) return -1;

    if (got_picture) {

        int pixfmt = AV_PIX_FMT_RGB24;
        int strides[] = {p->m->width * 3};
        if (grey) {
            pixfmt = AV_PIX_FMT_GRAY8;
            strides[0] = p->m->width;
        }

        struct SwsContext *img_convert_ctx;
        img_convert_ctx = sws_getCachedContext(NULL,
                                               p->m->width, p->m->height,
                                               p->codec_context->pix_fmt,
                                               p->m->width, p->m->height,
                                               pixfmt,
                                               SWS_BICUBIC, NULL, NULL,NULL);
        uint8_t *const planes[] = {img};
        sws_scale(img_convert_ctx,
              (const uint8_t * const*) ((AVPicture*)p->picture)->data,
              ((AVPicture*)p->picture)->linesize,
              0, p->m->height,
              planes, strides);


        sws_freeContext(img_convert_ctx);
        *ts = p->picture->pkt_pts;
        return 1;
    }
    return 0;
}
/*
int decode_seek(struct decode *p, uint64_t wanted, uint8_t *img, uint64_t *ts) {
    if (wanted) {
        wanted = videodb_closest_timestamp(p->ph, wanted, &p->next_time);
    }

    AVPacket pkt;
    int got_picture = 0;
    av_init_packet(&pkt);

    while(!got_picture) {
        if (videodb_play_frame(p->ph, p->next_time, &p->dbpkt)) return -1;
        pkt.data = p->dbpkt.data;
        pkt.size = p->dbpkt.len;
        pkt.pts  = p->dbpkt.systime;
        p->next_time = pkt.pts + 1;
        int len = avcodec_decode_video2(p->codec_context, p->picture,
                                        &got_picture, &pkt);
        assert(len>=0);
        if (wanted && wanted != p->picture->pkt_pts) {
            got_picture = 0;
        }
    }
    assert(p->rec.width == p->codec_context->width);
    assert(p->rec.height == p->codec_context->height);
    struct SwsContext *img_convert_ctx;
    img_convert_ctx = sws_getCachedContext(NULL,
                                           p->rec.width, p->rec.height,
                                           p->codec_context->pix_fmt,
                                           p->rec.width, p->rec.height,
                                           AV_PIX_FMT_RGB24,
                                           SWS_BICUBIC, NULL, NULL,NULL);
    uint8_t *const planes[] = {img};
    const int strides[] = {p->rec.width * 3};
    sws_scale(img_convert_ctx,
          (const uint8_t * const*) ((AVPicture*)p->picture)->data,
          ((AVPicture*)p->picture)->linesize,
          0, p->rec.height,
          planes, strides);


    sws_freeContext(img_convert_ctx);
    *ts = p->picture->pkt_pts;
    return 0;
}

int decode_next(struct decode *p, uint8_t *img, uint64_t *ts) {
    return decode_seek(p, 0, img, ts);
}


void decode_close(struct decode *p) {
    videodb_play_close(p->ph);
    videodb_close(p->db);
}

int decode_width(struct decode *p) {
    return p->rec.width;
}

int decode_height(struct decode *p) {
    return p->rec.height;
}

#ifdef MAIN
void main(int ac, char **av) {
    assert(ac==2);
    char *recid = av[1];
    struct decode *p = decode_open(videodb_open("video.lmdb"), recid);
    printf("%dx%d: %ld -> %ld\n", p->rec.width, p->rec.height,
           p->start_time, p->end_time);
    char *img = malloc(p->rec.width * p->rec.height * 3);
    uint64_t ts;
    time_t t0 = time(NULL);
    int fcnt = 0;
    while (decode_next(p, img, &ts)) {
        //printf("%ld\n", ts);
        fcnt++;
        if (fcnt%500 == 0) {
            printf("%f fps\n", ((double) fcnt) / ((double) (time(NULL) - t0)));
        }
    }
    decode_close(p);
}
#endif
*/
