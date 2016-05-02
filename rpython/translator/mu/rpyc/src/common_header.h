#ifndef _PY_COMMON_HEADER_H
#define _PY_COMMON_HEADER_H
#define PYPY_LONG_BIT 64
#define PYPY_LONGLONG_BIT 64
#define PYPY_STANDALONE pypy_g_entry_point
#define USE___THREAD 1
/***** Start of precommondefs.h *****/

/* This is extracted from pyconfig.h from CPython.  It sets the macros
   that affect the features we get from system include files.
   It must not #include anything. */

#ifndef __PYPY_PRECOMMONDEFS_H
#define __PYPY_PRECOMMONDEFS_H


/* Define on Darwin to activate all library features */
#define _DARWIN_C_SOURCE 1
/* This must be set to 64 on some systems to enable large file support. */
#define _FILE_OFFSET_BITS 64
/* Define on Linux to activate all library features */
#define _GNU_SOURCE 1
/* This must be defined on some systems to enable large file support. */
#define _LARGEFILE_SOURCE 1
/* Define on NetBSD to activate all library features */
#define _NETBSD_SOURCE 1
/* Define to activate features from IEEE Stds 1003.1-2001 */
#ifndef _POSIX_C_SOURCE
#  define _POSIX_C_SOURCE 200112L
#endif
/* Define on FreeBSD to activate all library features */
#define __BSD_VISIBLE 1
#define __XSI_VISIBLE 700
/* Windows: winsock/winsock2 mess */
#define WIN32_LEAN_AND_MEAN
#ifdef _WIN64
   typedef          __int64 Signed;
   typedef unsigned __int64 Unsigned;
#  define SIGNED_MIN LLONG_MIN
#else
   typedef          long Signed;
   typedef unsigned long Unsigned;
#  define SIGNED_MIN LONG_MIN
#endif

#if !defined(RPY_ASSERT) && !defined(RPY_LL_ASSERT)
#  define NDEBUG
#endif


/* All functions and global variables declared anywhere should use
   one of the following attributes:

   RPY_EXPORTED:  the symbol is exported out of libpypy-c.so.

   RPY_EXTERN:    the symbol is not exported out of libpypy-c.so, but
                  otherwise works like 'extern' by being available to
                  other C sources.

   static:        as usual, this means the symbol is local to this C file.

   Don't use _RPY_HIDDEN directly.  For tests involving building a custom
   .so, translator/tool/cbuild.py overrides RPY_EXTERN so that it becomes
   equal to RPY_EXPORTED.

   Any function or global variable declared with no attribute at all is
   a bug; please report or fix it.
*/
#ifdef __GNUC__
#  define RPY_EXPORTED extern __attribute__((visibility("default")))
#  define _RPY_HIDDEN  __attribute__((visibility("hidden")))
#else
#  define RPY_EXPORTED extern __declspec(dllexport)
#  define _RPY_HIDDEN  /* nothing */
#endif
#ifndef RPY_EXTERN
#  define RPY_EXTERN   extern _RPY_HIDDEN
#endif


#endif /* __PYPY_PRECOMMONDEFS_H */

/***** End of precommondefs.h *****/

/* using BoehmGCTransformer */
#define MALLOC_ZERO_FILLED 1
#define _REENTRANT 1
#define GC_LINUX_THREADS 1
#define GC_REDIRECT_TO_LOCAL 1
#include <gc/gc.h>
#include <sys/time.h>
#include <time.h>
#include <errno.h>
#include <sys/select.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/resource.h>
#include <sys/timeb.h>
#include <sys/wait.h>
#include <utime.h>
#include <sys/times.h>
#include <grp.h>
#include <dirent.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <signal.h>
#include <sys/utsname.h>
#include <pty.h>
#include <src/thread.h>
#include <stdio.h>
#include <src/dtoa.h>
#define RPY_WITH_GIL
RPY_EXTERN int get_errno ();
RPY_EXTERN void set_errno (int v);
#include "src/g_prerequisite.h"
#endif /* _PY_COMMON_HEADER_H*/
