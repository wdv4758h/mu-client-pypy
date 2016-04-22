def fac(n):
    if n in (0, 1):
        return 1
    return n * fac(n - 1)


def main_fac(argv):
    f = fac(int(argv[1]))
    print f
    return 0


def main_argv(argv):
    print argv
    return 0


def target(*args):
    return main_fac, None
