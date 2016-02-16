#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>
#include <errno.h>
#include <jerror.h>

#include "mjpg.h"

#define d_printf(...) fprintf(stderr, __VA_ARGS__)
//#define d_printf(...)

#ifndef N_RETRIES
#  define N_RETRIES 3
#endif

#ifndef MAX_STR_LEN
#  define MAX_STR_LEN 5
#endif

void skip_past_str( struct jpeg_decompress_struct *dec, char *str ) {
  unsigned char *p;
  unsigned int len=strlen(str);

  unsigned int times_failed = 0;

  while(1) {
    while (dec->src->bytes_in_buffer>0) {
      p=memchr(dec->src->next_input_byte,str[0],
               dec->src->bytes_in_buffer);
      if (p) {
        int d;
        times_failed = 0;
        d=((long)p)-((long)dec->src->next_input_byte);
        dec->src->next_input_byte=p;
        dec->src->bytes_in_buffer-=d;
        if (len<=dec->src->bytes_in_buffer) {
          if (!strncmp(str,(const char *)dec->src->next_input_byte,len)) {
            //dec->src->next_input_byte+=len;
            //dec->src->bytes_in_buffer-=len;
            return;
          }else {
            dec->src->next_input_byte++;
            dec->src->bytes_in_buffer--;
          }
        } else {
          char buf[2*MAX_STR_LEN];
          unsigned int l=dec->src->bytes_in_buffer;
          unsigned int i;

          memcpy(buf,dec->src->next_input_byte,l);
          dec->src->bytes_in_buffer=0;
          dec->src->fill_input_buffer(dec);

          if (dec->src->bytes_in_buffer<len) {
            d_printf("JPEG: Not enough data\n");
            dec->src->bytes_in_buffer=0;
            return;
          } else {
            memcpy(buf+l,dec->src->next_input_byte,len);
            buf[l+len]='\0';
            for (i=0; i<l; i++) {
              if (!strncmp(str,buf+i,len)) {
                d=len-l+i;
                dec->src->bytes_in_buffer-=d;
                dec->src->next_input_byte+=d;
                return;
              }
            }
          }
        }
      } else {
        if (++times_failed > 100) {
          d_printf("cannot find proper data\n");
          return;
        }
        dec->src->bytes_in_buffer=0;
      }
    }
    dec->src->fill_input_buffer(dec);
    if (dec->src->bytes_in_buffer<=2) return;
  }

}


typedef struct my_error_mgr * my_error_ptr;

METHODDEF(void)
my_error_exit (j_common_ptr cinfo)
{
  /* cinfo->err really points to a my_error_mgr struct, so coerce pointer */
  my_error_ptr myerr = (my_error_ptr) cinfo->err;

  /* Always display the message. */
  /* We could postpone this until after returning, if we chose. */
    //  (*cinfo->err->output_message) (cinfo);

  /* Return control to the setjmp point */
  longjmp(myerr->setjmp_buffer, 1);
}

int mjpg_open(struct mjpg *m, char *name, int type, int dataOrder) {
  FILE *fd;

  fd=fopen(name,"rb");
  if (!fd) {
    return ERROR_FILENOTFOUND;
  }

  return mjpg_open_fd(m,fd,type,dataOrder);
}

int mjpg_open_fd(struct mjpg *m, FILE *fd, int type, int dataOrder) {
  m->fd=fd;

  if (dataOrder==IMORDER_PLANAR && type!=IMTYPE_GRAY &&
      type!=IMTYPE_YCbCr) {
    d_printf("MJPG: Can only return raw data in planar format\n");
    return ERROR_ILLEGALARGUMENT;
  }

  m->cameraDecomp.err = jpeg_std_error(&(m->cameraJerr.pub));
  m->cameraJerr.pub.error_exit = my_error_exit;    
  jpeg_create_decompress(&(m->cameraDecomp));

  m->type=type;
  m->dataOrder=dataOrder;
  jpeg_stdio_src(&(m->cameraDecomp), fd);

  jpeg_save_markers(&(m->cameraDecomp),JPEG_COM,100);

  m->width=-1;
  m->nErr=0;
  m->pixels = NULL;

  return OK;
}

/// Reads the next frame into m.img
int mjpg_next_head(struct mjpg *m) {
  int ch;
  int i;
  char marker[] = { 0xFF, 0 };
  jpeg_saved_marker_ptr mrk;

  if (setjmp(m->cameraJerr.setjmp_buffer)) {
    /* Don't give up too easy, make 100 attempts. */
    if ( m->nErr++ > N_RETRIES || m->cameraJerr.pub.msg_code == JERR_INPUT_EMPTY) {
      /* If we get here, the JPEG code has signaled an error.
       * We need to clean up the JPEG object, close the input file, and return.
       */
      int c=m->cameraJerr.pub.msg_code;
      if ( c==JERR_EMPTY_IMAGE || c==JERR_INPUT_EMPTY || 
          c==JERR_INPUT_EOF   || c==JERR_NO_IMAGE )
        return ERROR_EOF;
      else
        return ERROR_FILEFORMAT;
    }
    jpeg_abort_decompress(&m->cameraDecomp);
    if ( m->cameraDecomp.src->bytes_in_buffer > 0 ) {
      m->cameraDecomp.src->next_input_byte++;
      m->cameraDecomp.src->bytes_in_buffer--;
    } else if (m->cameraJerr.pub.msg_code != JERR_INPUT_EMPTY) {
      d_printf("need more data\n");
      m->cameraDecomp.src->fill_input_buffer(&m->cameraDecomp);
    }
  }

  skip_past_str(&m->cameraDecomp, marker);
  m->start_position_in_file = ftell(m->fd)-m->cameraDecomp.src->bytes_in_buffer;
  
  jpeg_read_header(&m->cameraDecomp, TRUE);

  if (m->dataOrder==IMORDER_PLANAR_SUBX ||
      m->dataOrder==IMORDER_PLANAR_SUBXY)
    m->dataOrder=IMORDER_PLANAR;

  if (m->type==IMTYPE_GRAY) {
    ch=1;
    m->cameraDecomp.out_color_space=JCS_GRAYSCALE;
  } else {
    ch=3;
    if (m->type==IMTYPE_YCbCr)
      m->cameraDecomp.out_color_space=JCS_YCbCr; 
  }

  if (m->dataOrder==IMORDER_PLANAR) {
    m->cameraDecomp.raw_data_out=TRUE;
  }
      
  jpeg_start_decompress(&m->cameraDecomp);
  if (m->width==-1) {
    m->width = m->cameraDecomp.output_width;
    m->height = m->cameraDecomp.output_height;

    if (m->dataOrder==IMORDER_INTERLEAVED) {
      m->cameraBuffer[0] = (*m->cameraDecomp.mem->alloc_sarray)(
        (j_common_ptr) &m->cameraDecomp, 
        JPOOL_PERMANENT,
        m->width*ch,1);
    } else if (m->dataOrder==IMORDER_PLANAR) {
      for(i=0; i<m->cameraDecomp.num_components; i++) {
        m->cameraBuffer[i] = (*m->cameraDecomp.mem->alloc_sarray)(
          (j_common_ptr) &m->cameraDecomp, 
          JPOOL_PERMANENT,
          m->cameraDecomp.comp_info[i].width_in_blocks*DCTSIZE,
          m->cameraDecomp.comp_info[i].v_samp_factor*DCTSIZE);
      }
    } else {
      d_printf("MJPG: Unknown dataOrder %d\n",m->dataOrder);
      return ERROR_ILLEGALARGUMENT;
    }
  }

  m->timestamp_sec = m->timestamp_usec = 0;
  for (mrk=m->cameraDecomp.marker_list; mrk; mrk=mrk->next) {
    if (mrk->data_length>=7 && mrk->data[0]==0x0A && mrk->data[1]==0x01) {
      m->timestamp_sec  = (mrk->data[2]<<24) + (mrk->data[3]<<16) +
                              (mrk->data[4]<<8)  + (mrk->data[5]);
      m->timestamp_usec = mrk->data[6] * 10000;
    }
      /*
    if (mrk->data_length>=7 && mrk->data[0]==0x0A && mrk->data[1]==0x00) {
        printf("Hardware ID: 0x%.2x 0x%.2x\n", mrk->data[2], mrk->data[3]);
        printf("Firmware Version: %d.%d.%d\n", mrk->data[4], mrk->data[5], mrk->data[6]);
        printf("Serial: %.2x:%.2x:%.2x:%.2x:%.2x:%.2x\n", mrk->data[7], mrk->data[8], mrk->data[9], mrk->data[10], mrk->data[11], mrk->data[12]);
    }
    */
  }
  return OK;
 }

int mjpg_next_data(struct mjpg *m) {
  int x, y, i, ch;
  int row_stride;               /* physical row width in output buffer */

  if (m->type==IMTYPE_GRAY) {
    ch=1;
  } else {
    ch=3;
  }

  if (m->width != (int)m->cameraDecomp.output_width ||
      m->height != (int)m->cameraDecomp.output_height ||
      m->cameraDecomp.output_components != ch) {
    d_printf("Server returned wrong sized jpg: %dx%dx%d ",
             m->cameraDecomp.output_width,m->cameraDecomp.output_height,
             m->cameraDecomp.output_components);
    d_printf("expected was: %dx%dx%d\n", m->width, m->height, ch);
    return ERROR_FILEFORMAT;
  }

  if (m->dataOrder==IMORDER_INTERLEAVED) {
    row_stride = m->cameraDecomp.output_width *
      m->cameraDecomp.output_components;
    y=0;
    if (m->type==IMTYPE_YCbCr || m->type==IMTYPE_RGB ||
        m->type==IMTYPE_GRAY) {
      while (m->cameraDecomp.output_scanline < m->cameraDecomp.output_height) {
        jpeg_read_scanlines(&m->cameraDecomp, m->cameraBuffer[0], 1);
        memcpy(m->pixels+(y*m->width*ch),m->cameraBuffer[0][0],
               row_stride);
        y++;
      }
    } else if (m->type==IMTYPE_BGR) {
      while (m->cameraDecomp.output_scanline < m->cameraDecomp.output_height) {
        jpeg_read_scanlines(&m->cameraDecomp, m->cameraBuffer[0], 1);
        for (x=0; x<row_stride; x++) {
          m->pixels[y*m->width*ch+x]=
            m->cameraBuffer[0][0][x+2*(1-x%3)];
        }
        y++;
      }
    } else {
      d_printf("MJPG: Unknown image format %d\n", m->type);
      return ERROR_ILLEGALARGUMENT;
    }
  } else if (m->dataOrder==IMORDER_PLANAR) {
    unsigned char *y,*cb,*cr;
    y=m->pixels;
    cb=y+m->width*ch*m->height;
    cr=cb+m->width*ch*m->height;

    row_stride=m->cameraDecomp.max_v_samp_factor * DCTSIZE;
    if (m->cameraDecomp.num_components==1 && ch==1 && m->type==IMTYPE_GRAY) {
      // Greyscale images are fine
    } else if (m->cameraDecomp.num_components!=3 ||
        m->cameraDecomp.comp_info[0].h_samp_factor!=2 || 
        (m->cameraDecomp.comp_info[0].v_samp_factor!=1 &&
         m->cameraDecomp.comp_info[0].v_samp_factor!=2) ||
        m->cameraDecomp.comp_info[1].h_samp_factor!=1 ||
        m->cameraDecomp.comp_info[1].v_samp_factor!=1 ||
        m->cameraDecomp.comp_info[2].h_samp_factor!=1 ||
        m->cameraDecomp.comp_info[2].v_samp_factor!=1) {
      d_printf("MJPG: Can only handle 422 or 420 YCbCr jpegs\n");
      return 0;
    }
    m->dataOrder=IMORDER_PLANAR_SUBXY;
    
    while (m->cameraDecomp.output_scanline < m->cameraDecomp.output_height) {
    
      if (jpeg_read_raw_data(&m->cameraDecomp, m->cameraBuffer, row_stride)!=row_stride) {
        d_printf("MJPG: jpeg_read_raw_data failed");
        return ERROR_FILEFORMAT;
      }

      if (m->type==IMTYPE_YCbCr) {
        if (m->cameraDecomp.comp_info[0].v_samp_factor==1) {
          for (i=0; i<DCTSIZE/2; i++) {
            memcpy(y,m->cameraBuffer[0][2*i],
                   m->cameraDecomp.comp_info[0].width_in_blocks*DCTSIZE); 
            y+=m->cameraDecomp.comp_info[0].width_in_blocks*DCTSIZE;
            memcpy(y,m->cameraBuffer[0][2*i+1],
                   m->cameraDecomp.comp_info[0].width_in_blocks*DCTSIZE); 
            y+=m->cameraDecomp.comp_info[0].width_in_blocks*DCTSIZE;
          
            memcpy(cb,m->cameraBuffer[1][2*i],
                   m->cameraDecomp.comp_info[1].width_in_blocks*DCTSIZE);
            cb+=m->cameraDecomp.comp_info[1].width_in_blocks*DCTSIZE;
          
            memcpy(cr,m->cameraBuffer[2][2*i],
                   m->cameraDecomp.comp_info[2].width_in_blocks*DCTSIZE);
            cr+=m->cameraDecomp.comp_info[2].width_in_blocks*DCTSIZE;
          }
        } else {
          for (i=0; i<2*DCTSIZE; i++) {
            memcpy(y,m->cameraBuffer[0][i],
                   m->cameraDecomp.comp_info[0].width_in_blocks*DCTSIZE); 
            y+=m->cameraDecomp.comp_info[0].width_in_blocks*DCTSIZE;
          }
          for (i=0; i<DCTSIZE; i++) {
            memcpy(cb,m->cameraBuffer[1][i],
                   m->cameraDecomp.comp_info[1].width_in_blocks*DCTSIZE);
            cb+=m->cameraDecomp.comp_info[1].width_in_blocks*DCTSIZE;
          
            memcpy(cr,m->cameraBuffer[2][i],
                   m->cameraDecomp.comp_info[2].width_in_blocks*DCTSIZE);
            cr+=m->cameraDecomp.comp_info[2].width_in_blocks*DCTSIZE;
          }
        }
      } else if (m->type==IMTYPE_GRAY) {
        if (m->cameraDecomp.comp_info[0].v_samp_factor==1) {
          for (i=0; i<DCTSIZE/2; i++) {
            memcpy(y,m->cameraBuffer[0][2*i],
                   m->cameraDecomp.comp_info[0].width_in_blocks*DCTSIZE); 
            y+=m->cameraDecomp.comp_info[0].width_in_blocks*DCTSIZE;
            memcpy(y,m->cameraBuffer[0][2*i+1],
                   m->cameraDecomp.comp_info[0].width_in_blocks*DCTSIZE); 
            y+=m->cameraDecomp.comp_info[0].width_in_blocks*DCTSIZE;
          }
        } else {
          for (i=0; i<2*DCTSIZE; i++) {
            memcpy(y,m->cameraBuffer[0][i],
                   m->cameraDecomp.comp_info[0].width_in_blocks*DCTSIZE); 
            y+=m->cameraDecomp.comp_info[0].width_in_blocks*DCTSIZE;
          }
        }
        
      } else {
        d_printf("MJPG: Unknown image format %d\n", m->type);
      return ERROR_ILLEGALARGUMENT;
      }
    }
  } else {
    d_printf("MJPG: Unknown dataOrder %d\n",m->dataOrder);
    return ERROR_ILLEGALARGUMENT;
  }
  jpeg_finish_decompress(&m->cameraDecomp);
  m->stop_position_in_file = ftell(m->fd)-m->cameraDecomp.src->bytes_in_buffer;

  m->nErr = 0;
  return OK;
}

int mjpg_seek (struct mjpg *m, long offset) {
  if(!fseek(m->fd, offset, SEEK_SET)) {
    m->cameraDecomp.src->bytes_in_buffer=0;
    //m->cameraDecomp.src->fill_input_buffer(&m->cameraDecomp);
    return OK;
  } else {
    return ERROR_FAIL;
  }
}

/// Closes the file and frees all allocated memory
int mjpg_close(struct mjpg *m) {
  mjpg_close_fd(m);
  fclose(m->fd);
  return 0;
}
int mjpg_close_fd(struct mjpg *m) {
  jpeg_destroy_decompress(&m->cameraDecomp);
  return OK;
}
/*@}*/
