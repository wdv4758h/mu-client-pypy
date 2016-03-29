from ..mutyper import MuTyper
from rpython.rtyper.lltypesystem import lltype as llt
from ..muts import mutype as mut
from rpython.rtyper.lltypesystem.rstr import STR
from rpython.flowspace.model import Constant, Variable
from ..muts.muentity import MuGlobalCell, MuName
from rpython.rtyper.test.test_llinterp import gengraph
from ..ll2mu import *
from ..tools.textgraph import print_graph


def test_gcell():
    typer = MuTyper()

    string = "hello"
    ll_ps = llt.malloc(STR, len(string))
    ll_ps.hash = hash(string)
    for i in range(len(string)):
        ll_ps.chars[i] = string[i]

    cnst = Constant(ll_ps, llt.Ptr(STR))

    ldgcell = typer.proc_arg(cnst, None)

    assert isinstance(ldgcell, Variable)
    assert ldgcell.name == 'ldgclrefhybrpy_string_0'


def test_argtransform():
    def fac(n):
        if n in (0, 1):
            return 1
        return n * fac(n - 1)

    _, _, g = gengraph(fac, [int])
    print_graph(g)

    typer = MuTyper()
    typer.specialise(g)

    assert g.mu_name == MuName("fac")
    assert g.mu_type == mut.MuFuncRef(mut.MuFuncSig((mut.int64_t,), (mut.int64_t,)))
    assert g.startblock.mu_name == MuName("blk0", g)
    blk = g.startblock.exits[0].target
    op = blk.operations[1]  # v41 = direct_call((<* fn fac>), v40)
    assert isinstance(op.args[0].value, mut._mufuncref)
    assert op.result.mu_name == MuName(op.result.name, blk)
    assert op.result.mu_type == mut.int64_t
