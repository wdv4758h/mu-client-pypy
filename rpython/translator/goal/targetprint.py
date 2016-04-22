def fac(n):
    if n in (0, 1):
        return 1
    return n * fac(n - 1)


def main_fac(argv):
    f = fac(int(argv[1]))
    print f
    # return ord(str(f)[int(argv[2])]) - ord('0')
    return 0


def main_argv(argv):
    print argv
    return 0


def main_helloworld(argv):
    print "hellow world"
    return 0


def target(*args):
    return main_helloworld, None
