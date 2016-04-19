from rpython.flowspace.model import Variable, Constant
from rpython.rtyper.test.test_llinterp import gengraph
from ..exctran import MuExceptionTransformer
from rpython.mutyper.tools.textgraph import print_graph
from copy import copy


def test_exctran():
    class MyError(Exception):
        def __init__(self, msg):
            self.message = msg

    def raise_error_1():
        raise MyError("1st msg")

    def raise_error_2():
        raise MyError("2nd msg")

    def f(call_1):
        try:
            if call_1:
                raise_error_1()
            else:
                raise_error_2()
        except MyError as e:
            print e.message
        except IndexError:
            print "Caught"

    t, _, g = gengraph(f, [bool])
    print_graph(g)

    exctran = MuExceptionTransformer(t)
    blk = g.startblock.exits[0].target
    org_lnks = copy(blk.exits)
    exctran.exctran_block(blk, g)
    print_graph(g)

    assert blk.exits[1].args == []  # no extra args need to be carried.
    catblk = blk.exits[1].target
    assert hasattr(catblk, 'mu_excparam')
    assert catblk.operations[0].opname == 'cast_pointer'
    exc_t = catblk.operations[1].result
    exc_v = catblk.operations[2].result
    assert catblk.exits[0].args == [exc_t, exc_v]

    cmpblk_1 = catblk.exits[0].target
    assert cmpblk_1.inputargs == [exc_t, exc_v]
    assert cmpblk_1.operations[0].args[2].value == org_lnks[1].llexitcase
    assert cmpblk_1.exits[0].args == [exc_t, exc_v]
    assert cmpblk_1.exits[1].args == [exc_v]

    cmpblk_2 = cmpblk_1.exits[0].target
    assert cmpblk_2.inputargs == [exc_t, exc_v]
    assert cmpblk_2.operations[0].args[2].value == org_lnks[2].llexitcase
    assert cmpblk_2.exits[0].args == org_lnks[2].args   # []
    assert cmpblk_2.exits[1].args == [exc_t, exc_v]


def test_exctran_gcbench():
    # TODO: review test code.
    from rpython.translator.goal import gcbench
    gcbench.ENABLE_THREADS = False
    t, _, g = gengraph(gcbench.entry_point, [str])

    print_graph(g)
    exctran = MuExceptionTransformer(t)
    exctran.exctran(g)

    excblk = g.startblock.exits[0].target
    assert hasattr(excblk.raising_op, 'mu_exc')
    exc = excblk.raising_op.mu_exc

    norlnk = excblk.exits[0]
    assert exc.nor.blk is norlnk.target
    assert exc.nor.args is norlnk.args

    exclnk = excblk.exits[1]
    assert exc.exc.blk is exclnk.target
    assert exc.exc.args is exclnk.args
    assert isinstance(exclnk.target.mu_excparam, Variable)


def test_exctran_write():
    def fac(n):
        if n in (0, 1):
            v = 1
        else:
            v = n * fac(n - 1)
        print v
        return v

    _, _, g2 = gengraph(fac, [int])

    fncptr_write = \
        g2.startblock.exits[1].target.operations[2].args[0].value._obj.graph.startblock.exits[0].target. \
            operations[0].args[0].value._obj.graph.startblock.operations[0].args[0].value._obj.graph. \
            startblock.operations[13].args[0].value._obj.graph.startblock.exits[0].target.exits[0].target. \
            exits[0].target.exits[0].target.exits[0].target.exits[0].target.exits[0].target.exits[0].target. \
            operations[12].args[0].value._obj.graph.startblock.operations[1].args[0].value