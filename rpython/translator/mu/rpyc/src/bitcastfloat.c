#include <string.h>
#include <assert.h>

float pypy__uint2singlefloat(unsigned int x) {
    float ff;
    assert(sizeof(float) == 4 && sizeof(unsigned int) == 4);
    memcpy(&ff, &x, 4);
    return ff;
}

unsigned int pypy__singlefloat2uint(float x) {
    unsigned int ii;
    assert(sizeof(float) == 4 && sizeof(unsigned int) == 4);
    memcpy(&ii, &x, 4);
    return ii;
}
