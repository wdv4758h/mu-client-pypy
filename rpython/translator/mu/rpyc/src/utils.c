#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

#if defined(__linux__)
int stat64(const char* path, struct stat *buf) {
  return stat(path, buf);
}
#elif defined(__APPLE__)
#endif
