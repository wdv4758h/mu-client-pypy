from rpython.flowspace.model import Variable
from rpython.rtyper.test.test_llinterp import gengraph
from ..exctran import ExceptionTransformer
from rpython.mutyper.tools.textgraph import print_graph


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

    exctran = ExceptionTransformer(t)
    exctran.exctran(g)
    print_graph(g)

    blk = g.startblock.exits[0].target
    assert hasattr(blk.operations[-1], 'mu_exc')
    exc = blk.operations[-1].mu_exc
    assert exc
    assert exc.nor.blk is blk.exits[0].target
    assert exc.nor.args is blk.exits[0].args
    assert exc.exc.blk is blk.exits[1].target
    assert exc.exc.args is blk.exits[1].args
    assert exc.nor.blk.operations[0].opname == 'mu_throw'
    assert isinstance(exc.exc.blk.mu_excparam, Variable)
