#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

/** C system calls that differ between platforms. **/
#if defined(__linux__)

#define _PYPY_LINUX_PREFIX(fn) __pypy_mu_linux_ ## fn

int _PYPY_LINUX_PREFIX(stat64)(const char* path, struct stat *buf) { return stat(path, buf); }
int _PYPY_LINUX_PREFIX(fstat64)(int fd, struct stat *buf) { return fstat(fd, buf); }
int _PYPY_LINUX_PREFIX(lstat64)(const char *path, struct stat *buf) { return lstat(path, buf); }
int _PYPY_LINUX_PREFIX(mknod)(const char* pathname, mode_t mode, dev_t dev) { return mknod(pathname, mode, dev); }

extern char** environ;
char** _PYPY_LINUX_PREFIX(get_environ)() { return environ; }

#elif defined(__APPLE__)
#endif

/** C macros that are treated as functions. **/

#include <sys/wait.h>
#define _PYPY_MACRO_PREFIX(macro) __pypy_macro_ ## macro

#define _PYPY_WAITPID_MACRO(macro) int _PYPY_MACRO_PREFIX(macro) (int status) { return macro(status); }

_PYPY_WAITPID_MACRO(WCOREDUMP)
_PYPY_WAITPID_MACRO(WEXITSTATUS)
_PYPY_WAITPID_MACRO(WIFCONTINUED)
_PYPY_WAITPID_MACRO(WIFEXITED)
_PYPY_WAITPID_MACRO(WIFSIGNALED)
_PYPY_WAITPID_MACRO(WIFSTOPPED)
_PYPY_WAITPID_MACRO(WSTOPSIG)
_PYPY_WAITPID_MACRO(WTERMSIG)


#ifndef _BSD_SOURCE
#define _BSD_SOURCE
#endif
dev_t _PYPY_MACRO_PREFIX(makedev)(int maj, int min) { return makedev(maj, min); }
unsigned int _PYPY_MACRO_PREFIX(major)(dev_t dev) { return major(dev); }
unsigned int _PYPY_MACRO_PREFIX(minor)(dev_t dev) { return minor(dev); }

