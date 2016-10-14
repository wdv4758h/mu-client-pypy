from rpython.translator.mu.ll2mu import *


# TODO: write spec tests
def test_map_type_prim():
    ll2mu = LL2MuMapper()
    assert ll2mu.map_type(lltype.Signed) == mutype.MU_INT64
    assert ll2mu.map_type(lltype.Bool) == mutype.MU_INT8

    assert ll2mu.map_type(rffi.INT) == mutype.MU_INT32

def test_map_type_addr():
    ll2mu = LL2MuMapper()
    assert ll2mu.map_type(llmemory.Address) == mutype.MU_INT64

def test_map_type_struct():
    ll2mu = LL2MuMapper()
    LLT = lltype.GcStruct('Point', ('x', lltype.Signed), ('y', lltype.Signed))
    MuT = ll2mu.map_type(LLT)

    assert isinstance(MuT, mutype.MuStruct)
    assert len(MuT._names) == 3
    # a GC hash field is added to the front
    assert MuT._names[0] == LL2MuMapper.GC_IDHASH_FIELD[0]
    assert MuT[0] == mutype.MU_INT64
    assert MuT.x == mutype.MU_INT64

    # cached
    assert ll2mu.map_type(LLT) is MuT   # calling a second time return the same object

def test_map_type_ptr():
    ll2mu = LL2MuMapper()
    Point = lltype.GcStruct('Point', ('x', lltype.Signed), ('y', lltype.Signed))
    Node = lltype.GcForwardReference()
    PtrNode = lltype.Ptr(Node)
    Node.become(lltype.GcStruct("Node", ("payload", Point), ("next", PtrNode)))

    MuT = ll2mu.map_type(PtrNode)
    assert isinstance(MuT, mutype.MuRef)    # GcStruct result in Ref
    assert isinstance(MuT.TO, mutype.MuForwardReference)    # resolve later to break loop
    ll2mu.resolve_ptrs()
    assert isinstance(MuT.TO, mutype.MuStruct)
    assert MuT.TO.next is MuT   # loop preserved

    RawPoint = lltype.Struct('Point', ('x', lltype.Signed), ('y', lltype.Signed))
    RawPtr = lltype.Ptr(RawPoint)
    assert isinstance(ll2mu.map_type(RawPtr), mutype.MuUPtr)    # non-GCed Struct result in UPtr
