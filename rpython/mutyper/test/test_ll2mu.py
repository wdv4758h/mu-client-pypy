from ..ll2mu import ll2mu_ty
from rpython.rtyper.lltypesystem import lltype as ll
from rpython.mutyper.muts import mutype as mu
from rpython.rtyper.lltypesystem.rstr import STR
from rpython.rtyper.rclass import OBJECT


def test_ll2mu():
    assert ll2mu_ty(ll.Signed) == mu.int64_t

    S = ll2mu_ty(STR)
    assert isinstance(S, mu.MuHybrid)
    assert S._names == STR._names
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
