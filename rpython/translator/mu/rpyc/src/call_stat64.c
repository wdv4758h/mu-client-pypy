#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

int stat64(const char* path, struct stat *buf) {
  return stat(path, buf);
}
