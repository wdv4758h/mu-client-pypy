def main_helloworld(argv):
    print "hello world"
    return 0


def target(*args):
    return main_helloworld, None
