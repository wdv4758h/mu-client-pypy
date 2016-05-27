#include <errno.h>

int get_errno() {
  return errno;
}

void set_errno(int v) {
  errno = v;
}

