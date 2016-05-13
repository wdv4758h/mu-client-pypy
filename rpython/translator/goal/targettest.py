class A:
    def __init__(self):
        self._symtbl = {}

    def _get_sym(self, idx):
        return self._symtbl.get(idx, None)

    def _add_sym(self, idx, val):
        self._symtbl[idx] = val


def main(argv):
    d = {}

    d["foo"] = "FOO"
    d["bar"] = "BAR"
    # d["cowsay"] = "COWSAY"

    print d.get("foo", None)
    # print d.get("bar", None)
    # print d.get("cowsay", None)

    return 0


def target(*args):
    return main, None