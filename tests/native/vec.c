#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "vec.h"

struct vec { int items[VEC_MAX]; size_t n; };

vec *vec_new(void) { return calloc(1, sizeof(vec)); }
void vec_free(vec *v) { free(v); }
vec_status vec_push(vec *v, int x) {
    if (v->n >= VEC_MAX) return VEC_FULL;
    v->items[v->n++] = x;
    return VEC_OK;
}
int vec_get(const vec *v, size_t i) { return i < v->n ? v->items[i] : -1; }
size_t vec_len(const vec *v) { return v->n; }
long long vec_sum(const vec *v) {
    long long t = 0;
    for (size_t i = 0; i < v->n; i++) t += v->items[i];
    return t;
}
double vec_mean(const vec *v) { return v->n ? (double)vec_sum(v) / (double)v->n : 0.0; }
bool vec_contains(const vec *v, int x) {
    for (size_t i = 0; i < v->n; i++) if (v->items[i] == x) return true;
    return false;
}
const char *vec_describe(const vec *v) {
    static char buf[64];
    snprintf(buf, sizeof buf, "vec of %zu", v->n);
    return buf;
}
char *vec_join(const vec *v, const char *sep) {
    char *out = malloc(v->n * 24 + 1);
    out[0] = 0;
    for (size_t i = 0; i < v->n; i++) {
        char part[32];
        snprintf(part, sizeof part, "%s%d", i ? sep : "", v->items[i]);
        strcat(out, part);
    }
    return out;
}
void vec_free_string(char *s) { free(s); }
size_t vec_count_char(const char *s, char c) {
    size_t k = 0;
    for (; *s; s++) if (*s == c) k++;
    return k;
}
uint32_t vec_checksum(const uint8_t *data, size_t len) {
    uint32_t h = 2166136261u;
    for (size_t i = 0; i < len; i++) { h ^= data[i]; h *= 16777619u; }
    return h;
}
int vec_first_byte(const void *data, size_t len) { return len ? ((const uint8_t *)data)[0] : -1; }
int vec_dims(const vec *v, int *w, int *h) { *w = (int)v->n; *h = 1; return 0; }
int vec_logf(const char *fmt, ...) { return (int)strlen(fmt); }
vec_status vec_each(const vec *v, int (*fn)(int)) { for (size_t i = 0; i < v->n; i++) fn(v->items[i]); return VEC_OK; }
