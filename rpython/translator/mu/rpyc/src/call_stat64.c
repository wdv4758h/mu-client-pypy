#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

#if defined(_POSIX_C_SOURCE)
int stat64(const char* path, struct stat *buf) {
  return stat(path, buf);
}
#endif
