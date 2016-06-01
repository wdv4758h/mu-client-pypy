import weakref


class A:
    pass


a1 = A()
a1.hello = 5
w1 = weakref.ref(a1)
a2 = A()
a2.hello = 8
w2 = weakref.ref(a2)


def f(n):
    if n:
        r = w1
    else:
        r = w2
    return r().hello


def main(argv):
    print f(int(argv[1]))
    return 0


def target(*args):
    return main, None
