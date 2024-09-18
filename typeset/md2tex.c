#define MD4C_USE_UTF8
#include "md4c.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct MD_TEX_tag MD_TEX;
struct MD_TEX_tag {
  void (*process_output)(const MD_CHAR *, MD_SIZE, void *);
  void *userdata;
  unsigned flags;
  int table_col_level;
  int table_col_count;
  int list_item_level;
  int verbatim_type;
  char escape_map[256];
};

#define RENDER_VERBATIM(r, verbatim)                                           \
  render_verbatim((r), (verbatim), (MD_SIZE)(strlen(verbatim)))
static inline void render_verbatim(MD_TEX *r, const MD_CHAR *text,
                                   MD_SIZE size) {
  r->process_output(text, size, r->userdata);
}

#define NEED_TEX_ESC_FLAG 0x1
#define NEED_TEX_ESC(ch)                                                       \
  (r->escape_map[(unsigned char)(ch)] & NEED_TEX_ESC_FLAG)
static void render_tex_escaped(MD_TEX *r, const MD_CHAR *data, MD_SIZE size) {
  MD_OFFSET beg = 0;
  MD_OFFSET off = 0;
  while (1) {
    while (off + 3 < size && !NEED_TEX_ESC(data[off + 0]) &&
           !NEED_TEX_ESC(data[off + 1]) && !NEED_TEX_ESC(data[off + 2]) &&
           !NEED_TEX_ESC(data[off + 3]))
      off += 4;
    while (off < size && !NEED_TEX_ESC(data[off]))
      off++;
    if (off > beg)
      render_verbatim(r, data + beg, off - beg);
    if (off < size) {
      switch (data[off]) {
      case '~':
        RENDER_VERBATIM(r, "\\~{}");
        break;
      case '^':
        RENDER_VERBATIM(r, "\\^{}");
        break;
      case '#':
        RENDER_VERBATIM(r, "\\#");
        break;
      case '$':
        RENDER_VERBATIM(r, "\\$");
        break;
      case '%':
        RENDER_VERBATIM(r, "\\%");
        break;
      case '&':
        RENDER_VERBATIM(r, "\\&");
        break;
      case '{':
        RENDER_VERBATIM(r, "\\{");
        break;
      case '}':
        RENDER_VERBATIM(r, "\\}");
        break;
      case '_':
        RENDER_VERBATIM(r, "\\_");
        break;
      case '\\':
        RENDER_VERBATIM(r, "\\textbackslash");
        break;
      }
      off++;
    } else {
      break;
    }
    beg = off;
  }
}

static void render_attribute(MD_TEX *r, const MD_ATTRIBUTE *attr) {
  for (int i = 0; attr->substr_offsets[i] < attr->size; i++) {
    MD_TEXTTYPE type = attr->substr_types[i];
    MD_OFFSET off = attr->substr_offsets[i];
    MD_SIZE size = attr->substr_offsets[i + 1] - off;
    const MD_CHAR *text = attr->text + off;
    if (r->verbatim_type == 4)
      render_verbatim(r, text, size);
    else
      switch (type) {
      case MD_TEXT_NULLCHAR:
        break;
      case MD_TEXT_ENTITY:
        render_verbatim(r, text, size);
        break;
      default:
        render_tex_escaped(r, text, size);
        break;
      }
  }
}

static void render_open_code_block(MD_TEX *r, const MD_BLOCK_CODE_DETAIL *det) {
  RENDER_VERBATIM(r, "\\begin{verbatim}");
  if (det->lang.text != NULL) {
    RENDER_VERBATIM(r, "[language=");
    render_attribute(r, &det->lang);
    RENDER_VERBATIM(r, "]");
  }
  RENDER_VERBATIM(r, "\n");
}

static void render_open_table_block(MD_TEX *r,
                                    const MD_BLOCK_TABLE_DETAIL *det) {
  RENDER_VERBATIM(r, "\\begin{tabular}{");
  int cn = det->col_count;
  r->table_col_count = cn;
  while (cn-- != 0)
    RENDER_VERBATIM(r, "|l");
  RENDER_VERBATIM(r, "|}\n");
  RENDER_VERBATIM(r, "\\hline\n");
}

static void render_open_a_span(MD_TEX *r, const MD_SPAN_A_DETAIL *det) {
  RENDER_VERBATIM(r, "\\href{");
  r->verbatim_type = 4;
  render_attribute(r, &det->href);
  r->verbatim_type = 0;
  RENDER_VERBATIM(r, "}{");
}

static void render_open_img_span(MD_TEX *r, const MD_SPAN_IMG_DETAIL *det) {
  RENDER_VERBATIM(r, "\\begin{figure}[H]\n");
  RENDER_VERBATIM(r, "\\image{");
  render_attribute(r, &det->src);
  RENDER_VERBATIM(r, "}\\label{");
}

static void render_close_img_span(MD_TEX *r, const MD_SPAN_IMG_DETAIL *det) {
  RENDER_VERBATIM(r, "}\n");
  if (det->title.text != NULL) {
    RENDER_VERBATIM(r, "\\caption{");
    render_attribute(r, &det->title);
    RENDER_VERBATIM(r, "}\n");
  }
  RENDER_VERBATIM(r, "\\end{figure}\n");
}

static int enter_block_callback(MD_BLOCKTYPE type, void *detail,
                                void *userdata) {
  static const MD_CHAR *head[6] = {"\\title{",         "\\chapter{",
                                   "\\section{",       "\\subsection{",
                                   "\\subsubsection{", "\\paragraph{"};
  MD_TEX *r = (MD_TEX *)userdata;
  switch (type) {
  case MD_BLOCK_DOC:
    break;
  case MD_BLOCK_QUOTE:
    RENDER_VERBATIM(r, "\\begin{quote}\n");
    break;
  case MD_BLOCK_UL:
    RENDER_VERBATIM(r, "\\begin{enumerate}\n");
    r->list_item_level++;
    break;
  case MD_BLOCK_OL:
    RENDER_VERBATIM(r, "\\begin{itemize}\n");
    r->list_item_level++;
    break;
  case MD_BLOCK_LI:
    RENDER_VERBATIM(r, "\\item ");
    break;
  case MD_BLOCK_HR:
    RENDER_VERBATIM(r, "\\thematic\n");
    break;
  case MD_BLOCK_H:
    RENDER_VERBATIM(r, head[((MD_BLOCK_H_DETAIL *)detail)->level - 1]);
    break;
  case MD_BLOCK_CODE:
    render_open_code_block(r, (const MD_BLOCK_CODE_DETAIL *)detail);
    r->verbatim_type = 1;
    break;
  case MD_BLOCK_HTML:
    break;
  case MD_BLOCK_P:
    break;
  case MD_BLOCK_TABLE:
    render_open_table_block(r, (const MD_BLOCK_TABLE_DETAIL *)detail);
    break;
  case MD_BLOCK_THEAD:
    break;
  case MD_BLOCK_TBODY:
    break;
  case MD_BLOCK_TR:
    break;
  case MD_BLOCK_TH:
    if (++r->table_col_level == r->table_col_count)
      r->table_col_level = 0;
    break;
  case MD_BLOCK_TD:
    if (++r->table_col_level == r->table_col_count)
      r->table_col_level = 0;
    break;
  }
  return 0;
}

static int leave_block_callback(MD_BLOCKTYPE type, void *detail,
                                void *userdata) {
  MD_TEX *r = (MD_TEX *)userdata;
  switch (type) {
  case MD_BLOCK_DOC:
    break;
  case MD_BLOCK_QUOTE:
    RENDER_VERBATIM(r, "\\end{quote}\n");
    break;
  case MD_BLOCK_UL:
    RENDER_VERBATIM(r, "\\end{enumerate}\n");
    r->list_item_level = 0;
    break;
  case MD_BLOCK_OL:
    RENDER_VERBATIM(r, "\\end{itemize}\n");
    r->list_item_level = 0;
    break;
  case MD_BLOCK_LI:
    RENDER_VERBATIM(r, "\n");
    break;
  case MD_BLOCK_HR:
    break;
  case MD_BLOCK_H:
    RENDER_VERBATIM(r, "}\n");
    break;
  case MD_BLOCK_CODE:
    RENDER_VERBATIM(r, "\\end{verbatim}\n");
    r->verbatim_type = 0;
    break;
  case MD_BLOCK_HTML:
    break;
  case MD_BLOCK_P:
    if (r->list_item_level == 0)
      RENDER_VERBATIM(r, "\\par\n");
    break;
  case MD_BLOCK_TABLE:
    RENDER_VERBATIM(r, "\\end{tabular}\n");
    break;
  case MD_BLOCK_THEAD:
    break;
  case MD_BLOCK_TBODY:
    break;
  case MD_BLOCK_TR:
    RENDER_VERBATIM(r, " \\\\\n\\hline\n");
    break;
  case MD_BLOCK_TH:
    if (r->table_col_level != 0)
      RENDER_VERBATIM(r, " & ");
    break;
  case MD_BLOCK_TD:
    if (r->table_col_level != 0)
      RENDER_VERBATIM(r, " & ");
    break;
  }
  return 0;
}

static int enter_span_calback(MD_SPANTYPE type, void *detail, void *userdata) {
  MD_TEX *r = (MD_TEX *)userdata;
  switch (type) {
  case MD_SPAN_EM:
    RENDER_VERBATIM(r, "\\textit{");
    break;
  case MD_SPAN_STRONG:
    RENDER_VERBATIM(r, "\\textbf{");
    break;
  case MD_SPAN_U:
    RENDER_VERBATIM(r, "\\underline{");
    break;
  case MD_SPAN_A:
    render_open_a_span(r, (MD_SPAN_A_DETAIL *)detail);
    break;
  case MD_SPAN_IMG:
    render_open_img_span(r, (MD_SPAN_IMG_DETAIL *)detail);
    break;
  case MD_SPAN_CODE:
    RENDER_VERBATIM(r, "\\verb!");
    r->verbatim_type = 2;
    break;
  case MD_SPAN_DEL:
    RENDER_VERBATIM(r, "\\del{");
    break;
  case MD_SPAN_LATEXMATH:
    RENDER_VERBATIM(r, "$");
    r->verbatim_type = 3;
    break;
  case MD_SPAN_LATEXMATH_DISPLAY:
    RENDER_VERBATIM(r, "$$");
    r->verbatim_type = 3;
    break;
  case MD_SPAN_WIKILINK:
    break;
  }
  return 0;
}

static int leave_span_calback(MD_SPANTYPE type, void *detail, void *userdata) {
  MD_TEX *r = (MD_TEX *)userdata;
  switch (type) {
  case MD_SPAN_EM:
    RENDER_VERBATIM(r, "}");
    break;
  case MD_SPAN_STRONG:
    RENDER_VERBATIM(r, "}");
    break;
  case MD_SPAN_U:
    RENDER_VERBATIM(r, "}");
    break;
  case MD_SPAN_A:
    RENDER_VERBATIM(r, "}");
    break;
  case MD_SPAN_IMG:
    render_close_img_span(r, (MD_SPAN_IMG_DETAIL *)detail);
    break;
  case MD_SPAN_CODE:
    RENDER_VERBATIM(r, "!");
    r->verbatim_type = 0;
    break;
  case MD_SPAN_DEL:
    RENDER_VERBATIM(r, "}");
    break;
  case MD_SPAN_LATEXMATH:
    RENDER_VERBATIM(r, "$");
    r->verbatim_type = 0;
    break;
  case MD_SPAN_LATEXMATH_DISPLAY:
    RENDER_VERBATIM(r, "$$");
    r->verbatim_type = 0;
    break;
  case MD_SPAN_WIKILINK:
    break;
  }
  return 0;
}

static int text_callback(MD_TEXTTYPE type, const MD_CHAR *text, MD_SIZE size,
                         void *userdata) {
  MD_TEX *r = (MD_TEX *)userdata;
  if (r->verbatim_type != 0)
    render_verbatim(r, text, size);
  else
    switch (type) {
    case MD_TEXT_NULLCHAR:
      break;
    case MD_TEXT_BR:
      RENDER_VERBATIM(r, "\\par");
      break;
    case MD_TEXT_SOFTBR:
      RENDER_VERBATIM(r, "\n");
      break;
    case MD_TEXT_HTML:
      render_verbatim(r, text, size);
      break;
    case MD_TEXT_ENTITY:
      render_verbatim(r, text, size);
      break;
    default:
      render_tex_escaped(r, text, size);
      break;
    }
  return 0;
}

int md_tex(const MD_CHAR *input, MD_SIZE input_size,
           void (*process_output)(const MD_CHAR *, MD_SIZE, void *),
           void *userdata, unsigned parser_flags, unsigned renderer_flags) {
  MD_TEX render = {.process_output = process_output,
                   .userdata = userdata,
                   .flags = renderer_flags,
                   .table_col_level = 0,
                   .table_col_count = -1,
                   .list_item_level = 0,
                   .verbatim_type = 0,
                   .escape_map = {0}};
  MD_PARSER parser = {.abi_version = 0,
                      .flags = parser_flags,
                      .enter_block = enter_block_callback,
                      .leave_block = leave_block_callback,
                      .enter_span = enter_span_calback,
                      .leave_span = leave_span_calback,
                      .text = text_callback,
                      .debug_log = NULL,
                      .syntax = NULL};
  for (int i = 0; i < 256; i++) {
    unsigned char ch = (unsigned char)i;
    if (strchr("~^#$%&{}_\\", ch) != NULL)
      render.escape_map[i] |= NEED_TEX_ESC_FLAG;
  }
  return md_parse(input, input_size, &parser, (void *)&render);
}

static unsigned parser_flags = 0;
static unsigned renderer_flags = 0;

struct membuffer {
  char *data;
  size_t asize;
  size_t size;
};

static void membuf_init(struct membuffer *buf, MD_SIZE new_asize) {
  buf->size = 0;
  buf->asize = new_asize;
  buf->data = malloc(buf->asize);
  if (buf->data == NULL) {
    fprintf(stderr, "membuf_init: malloc() failed.\n");
    exit(1);
  }
}

static void membuf_fini(struct membuffer *buf) {
  if (buf->data)
    free(buf->data);
}

static void membuf_grow(struct membuffer *buf, size_t new_asize) {
  buf->data = realloc(buf->data, new_asize);
  if (buf->data == NULL) {
    fprintf(stderr, "membuf_grow: realloc() failed.\n");
    exit(1);
  }
  buf->asize = new_asize;
}

static void membuf_append(struct membuffer *buf, const char *data,
                          MD_SIZE size) {
  if (buf->asize < buf->size + size)
    membuf_grow(buf, buf->size + buf->size / 2 + size);
  memcpy(buf->data + buf->size, data, size);
  buf->size += size;
}

static void process_output(const MD_CHAR *text, MD_SIZE size, void *userdata) {
  membuf_append((struct membuffer *)userdata, text, size);
}

static int process_file(FILE *in, FILE *out) {
  size_t n;
  struct membuffer buf_in = {0};
  struct membuffer buf_out = {0};
  int ret = -1;
  clock_t t0, t1;
  unsigned p_flags = parser_flags;
  unsigned r_flags = renderer_flags;
  membuf_init(&buf_in, 32 * 1024);
  while (1) {
    if (buf_in.size >= buf_in.asize)
      membuf_grow(&buf_in, buf_in.asize + buf_in.asize / 2);
    n = fread(buf_in.data + buf_in.size, 1, buf_in.asize - buf_in.size, in);
    if (n == 0)
      break;
    buf_in.size += n;
  }
  membuf_init(&buf_out, (MD_SIZE)(buf_in.size + buf_in.size / 8 + 64));
  t0 = clock();
  ret = md_tex(buf_in.data, (MD_SIZE)buf_in.size, process_output,
               (void *)&buf_out, p_flags, r_flags);
  t1 = clock();
  if (ret != 0) {
    fprintf(stderr, "Parsing failed.\n");
    goto out;
  }
  fwrite(buf_out.data, 1, buf_out.size, out);
  if (t0 != (clock_t)-1 && t1 != (clock_t)-1) {
    double elapsed = (double)(t1 - t0) / CLOCKS_PER_SEC;
    if (elapsed < 1)
      fprintf(stderr, "Time spent on parsing: %7.2f ms.\n", elapsed * 1e3);
    else
      fprintf(stderr, "Time spent on parsing: %6.3f s.\n", elapsed);
  }
  ret = 0;
out:
  membuf_fini(&buf_in);
  membuf_fini(&buf_out);
  return ret;
}

int main(int argc, char **argv) {
  if (argc != 3)
    return 0;
  FILE *in = fopen(*++argv, "rb");
  FILE *out = fopen(*++argv, "wt");
  parser_flags |= MD_FLAG_TABLES;
  parser_flags |= MD_FLAG_STRIKETHROUGH;
  parser_flags |= MD_FLAG_UNDERLINE;
  parser_flags |= MD_FLAG_LATEXMATHSPANS;
  process_file(in, out);
}
