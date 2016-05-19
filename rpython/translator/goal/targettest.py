from pyhaskell.interpreter.jscparser import parse_js


def main(argv):
    parse_js("")
    return 0


def target(*args):
    return main, None
