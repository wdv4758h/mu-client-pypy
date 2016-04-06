def fac(n):
    if n in (0, 1):
        return 1
    return n * fac(n - 1)


def main(argv):
    return fac(int(argv[0]))


def target(*args):
    return main, None
