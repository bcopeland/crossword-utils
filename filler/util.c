#include <stdlib.h>
#include <string.h>
#include "util.h"

void *xstrdup(const char *ptr)
{
	void *ret = strdup(ptr);
	if (!ret)
		exit(1);
	return ret;
}

void *xrealloc(void *ptr, size_t size)
{
	void *ret = realloc(ptr, size);
	if (!ret)
		exit(1);
	return ret;
}

void *xmalloc(size_t size)
{
	void *ret = malloc(size);
	if (!ret)
		exit(1);
	return ret;
}

void *xmemdup(void *ptr, size_t size)
{
	void *ret = xmalloc(size);
	memcpy(ret, ptr, size);
	return ret;
}

void *xcalloc(size_t nmemb, size_t size)
{
	void *ret = calloc(nmemb, size);
	if (!ret)
		exit(1);
	return ret;
}

