unsigned long pypy__rotateLeft(unsigned long x, long n) {
    unsigned int x1 = x;    /* arithmetic directly on int */
    int n1 = n;
    return (x1 << n1) | (x1 >> (32-n1));
}
