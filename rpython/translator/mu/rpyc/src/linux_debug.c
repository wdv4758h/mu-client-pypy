#ifdef __linux__
#include <string.h>
#include <assert.h>
#include <sys/prctl.h>

/* If we have an old Linux kernel (or compile with old system headers),
   the following two macros are not defined.  But we would still like
   a pypy translated on such a system to run on a more modern system. */
#ifndef PR_SET_PTRACER
#  define PR_SET_PTRACER 0x59616d61
#endif
#ifndef PR_SET_PTRACER_ANY
#  define PR_SET_PTRACER_ANY ((unsigned long)-1)
#endif
void pypy__allow_attach(void) {
    prctl(PR_SET_PTRACER, PR_SET_PTRACER_ANY);
}
#endif
