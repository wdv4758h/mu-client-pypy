def main_helloworld(argv):
    # print "hello world"
    print hex(int(argv[1]))
    return 0


def target(*args):
    return main_helloworld, None
