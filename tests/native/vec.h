#ifndef VEC_H
#define VEC_H
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#define VEC_MAX 8
#define VEC_NAME "vec"
#define VEC_RATIO 3.25

typedef enum { VEC_OK = 0, VEC_EMPTY = 1, VEC_FULL = 2 } vec_status;

/* an opaque growable list of ints */
typedef struct vec vec;

vec *vec_new(void);
void vec_free(vec *v);
vec_status vec_push(vec *v, int x);
int vec_get(const vec *v, size_t i);
size_t vec_len(const vec *v);
long long vec_sum(const vec *v);
double vec_mean(const vec *v);
bool vec_contains(const vec *v, int x);

/* strings */
const char *vec_describe(const vec *v);          /* points at a static buffer */
char *vec_join(const vec *v, const char *sep);   /* malloc'd; release with vec_free_string */
void vec_free_string(char *s);
size_t vec_count_char(const char *s, char c);

/* bytes */
uint32_t vec_checksum(const uint8_t *data, size_t len);
int vec_first_byte(const void *data, size_t len);

/* not wrappable automatically */
int vec_dims(const vec *v, int *w, int *h);      /* output parameters */
int vec_logf(const char *fmt, ...);              /* variadic */
vec_status vec_each(const vec *v, int (*fn)(int));  /* callback */
#endif
