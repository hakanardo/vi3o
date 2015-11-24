#include "mkv.h"

struct decode;
struct decode *decode_open(struct mkv *m);
int decode_frame(struct decode *p, struct mkv_frame *frm, uint8_t *img, uint64_t *ts, int grey);


