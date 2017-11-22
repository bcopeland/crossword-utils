#ifndef UTIL_H
#define UTIL_H
void *xstrdup(const char *ptr);
void *xrealloc(void *ptr, size_t size);
void *xmalloc(size_t size);
void *xmemdup(void *ptr, size_t size);
void *xcalloc(size_t nmemb, size_t size);
#endif
