def fac(n):
    if n in (0, 1):
        return 1
    return n * fac(n - 1)


def main(argv):
    # return fac(int(argv[1]))
    return len(str(fac(int(argv[1]))))


def target(*args):
    return main, None
