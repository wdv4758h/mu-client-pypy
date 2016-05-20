from random import randint


class A(object):
    a = 42

    def __init__(self, x):
        self.x = x


class B(A):
    b = "b"

    def __init__(self, x, y):
        A.__init__(self, x)
        self.y = y

objs = [A("A type 0"), B("B type 0", "dummy"), A("A type 1"), B("B type 1", "dummy again")]
dic = {}
for o in objs:
    dic[o] = randint(0, 1000)


def main(argv):
    obj = objs[int(argv[1])]
    print obj.x
    if isinstance(obj, B):
        print obj.y
    try:
        print dic[obj]
    except KeyError:
        print "Object key not found."
    return 0


def target(*args):
    return main, None
