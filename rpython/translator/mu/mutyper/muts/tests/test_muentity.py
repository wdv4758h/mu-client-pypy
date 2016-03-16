from ..muentity import MuName, SCOPE_GLOBAL
from rpython.rtyper.test.test_llinterp import gengraph
from rpython.flowspace.model import FunctionGraph


def test_muname():
    n1 = MuName("gbl")
    assert n1.scope == SCOPE_GLOBAL

    # Test duplication
    n2 = MuName("gbl")
    assert n2 == n1     # same name -> same name instance

    def f(x):
        return x + 1

    # A realistic test
    _, _, g = gengraph(f, [int])
    assert isinstance(g, FunctionGraph)
    g.mu_name = MuName(g.name)

    for idx, blk in enumerate(list(g.iterblocks())):
        blk.mu_name = MuName("blk%d" % idx, g)
        for v in blk.getvariables():
            v.mu_name = MuName(v.name, blk)

    v = g.startblock.getvariables()[0]
    assert repr(v.mu_name) == '@f.blk0.x_0'
