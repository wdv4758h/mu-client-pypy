from ..ll2mu import ll2mu_ty, ll2mu_val
from rpython.rtyper.lltypesystem import lltype as ll
from rpython.mutyper.muts import mutype as mu
from rpython.rtyper.lltypesystem.rstr import STR
from rpython.rtyper.rclass import OBJECT
from rpython.rtyper.test.test_llinterp import gengraph


def test_ll2mu_ty():
    assert ll2mu_ty(ll.Signed) == mu.int64_t

    S = ll2mu_ty(STR)
    assert isinstance(S, mu.MuHybrid)
    assert hasattr(S, 'length')
    assert S.length == mu.int64_t
    assert S.hash == mu.int64_t
    assert S.chars == mu.int8_t

    PS = ll2mu_ty(ll.Ptr(STR))
    assert isinstance(PS, mu.MuRef)
    assert PS.TO == S

    OBJ = ll2mu_ty(OBJECT)
    assert OBJ.typeptr.TO.instantiate.Sig.ARGS[0].TO == OBJ

    A = ll2mu_ty(ll.Array(ll.Char))
    assert isinstance(A, mu.MuHybrid)

    FA = ll2mu_ty(ll.FixedSizeArray(ll.Char, 10))
    assert isinstance(FA, mu.MuArray)
    assert FA.length == 10


def test_ll2mu_val():
    assert ll2mu_val(1, ll.Signed) == mu._muprimitive(mu.int64_t, 1)

    string = "hello"
    ll_ps = ll.malloc(STR, len(string))
    ll_ps.hash = hash(string)
    for i in range(len(string)):
        ll_ps.chars[i] = string[i]

    mu_rs = ll2mu_val(ll_ps)
    assert isinstance(mu_rs, mu._muref)
    mu_irs = mu_rs._getiref()
    assert isinstance(mu_irs._obj, mu._muhybrid)
    assert isinstance(mu_irs.length._obj, mu._muprimitive)
    assert mu_irs.hash._obj.val == ll_ps.hash
    assert mu_irs.length._obj.val == len(string)
    for i in range(len(string)):
        mu_irs.chars[i]._obj.val == ord(string[i])


def test_ll2mu_fncptr():
    def fac(n):
        if n in (0, 1):
            return 1
        return n * fac(n - 1)

    def f(x):
        return x + fac(x)

    _, _, g = gengraph(f, [int])

    op = g.startblock.operations[0]
    assert op.opname == 'direct_call'
    mut = ll2mu_ty(op.args[0].concretetype)
    muv = ll2mu_val(op.args[0].value)
    assert isinstance(mut, mu.MuFuncRef)
    assert isinstance(muv, mu._mufuncref)
    assert muv.graph == op.args[0].value._obj.graph

    # An example of no graphs.
    def fac2(n):
        if n in (0, 1):
            v = 1
        else:
            v = n * fac(n - 1)
        print v
        return v

    _, _, g2 = gengraph(fac2, [int])

    fncptr_write = \
        g2.startblock.exits[1].target.operations[2].args[0].value._obj.graph.startblock.exits[0].target. \
            operations[0].args[0].value._obj.graph.startblock.operations[0].args[0].value._obj.graph. \
            startblock.operations[13].args[0].value._obj.graph.startblock.exits[0].target.exits[0].target. \
            exits[0].target.exits[0].target.exits[0].target.exits[0].target.exits[0].target.exits[0].target. \
            operations[12].args[0].value._obj.graph.startblock.operations[2].args[0].value
    muv = ll2mu_val(fncptr_write)
    assert muv.fncname == "write"
    assert muv.graph is None
    assert muv.compilation_info == fncptr_write._obj.compilation_info
