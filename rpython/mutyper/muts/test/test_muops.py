from rpython.mutyper.muts.muops import *
from rpython.mutyper.muts.mutype import *
from rpython.rtyper.test.test_llinterp import gengraph
from rpython.mutyper.tools.textgraph import print_graph
from ...ll2mu import ll2mu_ty, ll2mu_val


def test_binaryops():
    a = Variable('a')
    b = Variable('b')
    a.mu_name = MuName(a.name)
    b.mu_name = MuName(b.name)
    a.mu_type = int64_t
    b.mu_type = int64_t
    op = ADD(a, b)
    assert op.result.mu_type == int64_t
    assert isinstance(op, MuOperation)
    assert repr(op) == "@rtn_0 = ADD <@i64> @a_0 @b_0 "


def test_call():
    def fac(n):
        if n in (0, 1):
            return 1
        return n * fac(n - 1)

    _, _, g = gengraph(fac, [int])

    g.mu_name = MuName(g.name)
    g.mu_type = MuFuncRef(MuFuncSig([ll2mu_ty(arg.concretetype) for arg in g.startblock.inputargs],
                                    [ll2mu_ty(g.returnblock.inputargs[0].concretetype)]))

    g.startblock.mu_name = MuName('blk0', g)
    blk = g.startblock.exits[0].target
    blk.mu_name = MuName('blk1', g)

    llop = g.startblock.exits[0].target.operations[1]   # v7 = direct_call((<* fn fac>), v6)
    v = llop.args[1]
    v.mu_type = ll2mu_ty(v.concretetype)
    v.mu_name = MuName(v.name, blk)
    r = llop.result
    r.mu_type = ll2mu_ty(r.concretetype)
    r.mu_name = MuName(r.name, blk)
    callee = llop.args[0]
    callee.mu_type = ll2mu_ty(callee.concretetype)
    callee.value = ll2mu_val(llop.args[0].value).graph
    assert callee.value == g
    muop = CALL(callee.value, [v], result=r)
    assert muop.result.mu_type == int64_t
    assert repr(muop) == "%v7 = CALL <@sig_i64_i64> @fac (%v6)  "

