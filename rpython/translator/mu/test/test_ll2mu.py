from rpython.translator.mu.ll2mu import *


# TODO: write spec tests
def test_map_type_prim():
    ll2mu = LL2MuTypeMapper()
    assert ll2mu.map(lltype.Signed) == mutype.MU_INT64
    assert ll2mu.map(lltype.Bool) == mutype.MU_INT8

    assert ll2mu.map(rffi.INT) == mutype.MU_INT32

def test_map_type_addr():
    ll2mu = LL2MuTypeMapper()
    assert ll2mu.map(llmemory.Address) == mutype.MU_INT64

def test_map_type_struct():
    ll2mu = LL2MuTypeMapper()
    LLT = lltype.GcStruct('Point', ('x', lltype.Signed), ('y', lltype.Signed))
    MuT = ll2mu.map(LLT)

    assert isinstance(MuT, mutype.MuStruct)
    assert len(MuT._names) == 3
    # a GC hash field is added to the front
    assert MuT._names[0] == LL2MuTypeMapper.GC_IDHASH_FIELD[0]
    assert MuT[0] == mutype.MU_INT64
    assert MuT.x == mutype.MU_INT64

    # cached
    assert ll2mu.map(LLT) is MuT   # calling a second time return the same object

def test_map_type_hybrid():
    ll2mu = LL2MuTypeMapper()
    from rpython.rtyper.lltypesystem.rstr import STR
    MuT = ll2mu.map(STR)

    assert isinstance(MuT, mutype.MuHybrid)
    assert MuT._vartype == mutype._MuMemArray(mutype.MU_INT8)

def test_map_type_ptr():
    ll2mu = LL2MuTypeMapper()
    Point = lltype.GcStruct('Point', ('x', lltype.Signed), ('y', lltype.Signed))
    Node = lltype.GcForwardReference()
    PtrNode = lltype.Ptr(Node)
    Node.become(lltype.GcStruct("Node", ("payload", Point), ("next", PtrNode)))

    MuT = ll2mu.map(PtrNode)
    assert isinstance(MuT, mutype.MuRef)    # GcStruct result in Ref
    assert isinstance(MuT.TO, mutype.MuForwardReference)    # resolve later to break loop
    ll2mu.resolve_ptrs()
    assert isinstance(MuT.TO, mutype.MuStruct)
    assert MuT.TO.next is MuT   # loop preserved

    RawPoint = lltype.Struct('Point', ('x', lltype.Signed), ('y', lltype.Signed))
    RawPtr = lltype.Ptr(RawPoint)
    assert isinstance(ll2mu.map(RawPtr), mutype.MuUPtr)    # non-GCed Struct result in UPtr

def test_map_type_funcptr():
    from rpython.rtyper.rclass import OBJECTPTR
    ll2mu = LL2MuTypeMapper()
    MuT = ll2mu.map(OBJECTPTR)
    ll2mu.resolve_ptrs()
    FncRef = MuT.TO.typeptr.TO.instantiate
    Sig = FncRef.sig
    assert Sig.ARGS == ()
    assert Sig.RESULTS == (MuT, )
