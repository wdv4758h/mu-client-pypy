from ..ll2mu import ll2mu_ty, ll2mu_val
from rpython.rtyper.lltypesystem import lltype as ll
from rpython.mutyper.muts import mutype as mu
from rpython.rtyper.lltypesystem.rstr import STR
from rpython.rtyper.rclass import OBJECT


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
