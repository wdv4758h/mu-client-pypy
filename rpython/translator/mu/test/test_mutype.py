import pytest
from rpython.translator.mu.mutype import *
from rpython.translator.mu import mutype


def test_primitives():
    assert MU_INT1.BITS == 1
    assert MU_INT128.BITS == 128
    true = mu_int1(1)
    false = mu_int1(0)
    assert true
    assert not false

    x = mu_int64(3)
    y = mu_int64(4)
    assert x + y == 7   # can add, can compare with python value
    assert type(x + 4) is mu_int64

    assert x != mu_int8(8)  # type equality included

    m = mu_int64(256)
    assert mu_int8(m) == mu_int8(0)     # wrap around 'cast'


def test_get_int64s():
    a = mu_int128(0x1234567890ABCD1234567890ABCDEF)
    assert a.get_uint64s() == \
           map(mu_int64, [0x1234567890ABCDEF, 0x1234567890ABCD])


def test_containers():
    S = MuStruct("Point", ("x", MU_INT64), ("y", MU_INT64))
    assert S.x == MU_INT64
    assert S[0] == MU_INT64
    s = S._allocate()

    assert s.y == mu_int64(0)   # default value
    s.x = mu_int64(10)
    assert s.x == mu_int64(10)
    hash(s.x) == mu_int64(10)
    assert s[0] == s.x

    H = MuHybrid("String", ("hash", MU_INT64),
                 ("length", MU_INT64), ("chars", MU_INT8))

    assert H._varfld == "chars"
    assert H[-1] == MU_INT64    # length field
    from rpython.translator.mu.mutype import _MuMemArray, _mumemarray
    assert isinstance(H.chars, _MuMemArray)
    assert H.chars.OF is MU_INT8

    h = H._container_example()
    assert isinstance(h.chars, _mumemarray)
    h.chars[0] == mu_int8(0)
    with pytest.raises(AssertionError):
        h.chars[0] = mu_int64(ord('c'))
    h.chars[0] = mu_int8(ord('c'))
    assert h.chars[0] == mu_int8(ord('c'))

    A = MuArray(S, 5)
    assert A.OF == S
    assert A.length == 5
    a = A._allocate()
    with pytest.raises(AttributeError):
        a.item0
    from rpython.translator.mu.mutype import _mustruct
    assert isinstance(a[0], _mustruct)
    assert a[0].x == mu_int64(0)


def test_mutypeOf():
    x = mu_int64(10)
    assert mutypeOf(x) is MU_INT64

    with pytest.raises(TypeError):
        mutypeOf(10)

    S = MuStruct("Point", ("x", MU_INT64), ("y", MU_INT64))
    s = S._allocate()
    assert mutypeOf(s) == S


def test_func():
    F = MuFuncType([MU_INT64, MU_INT64], [MU_INT8, MU_FLOAT])
    assert F.RESULTS == (MU_INT8, MU_FLOAT)
    f = F._container_example()
    assert f._callable() == (mu_int8(0), mu_float(0.0))


def test_cannot_inline_opaque():
    Stack = MuOpaqueType("Stack")
    with pytest.raises(TypeError):
        MuArray(Stack, 5)
    with pytest.raises(TypeError):
        MuStruct('tmp', ('stk', Stack))
    with pytest.raises(TypeError):
        MuHybrid('tmp', ('stk', Stack))


def test_opaquereference():
    IRNode = MuOpaqueType("IRNode")

    # enforce Ref, IRef and UPtr can not refer to Opaque types
    with pytest.raises(TypeError):
        MuRef(IRNode)
    with pytest.raises(TypeError):
        MuIRef(IRNode)
    with pytest.raises(TypeError):
        MuUPtr(IRNode)

    with pytest.raises(TypeError):
        MuOpaqueRef(MU_INT64)  # opaque reference can only refer to MuOpaque type

    IRNodeRef = MuOpaqueRef(IRNode)
    refNULL = IRNodeRef._allocate()
    assert not refNULL  # NULL reference
    assert mutypeOf(refNULL) == IRNodeRef  # has _TYPE
    with pytest.raises(AttributeError):
        refNULL._cast_to(MuRef(MU_INT64))   # can not cast opaque reference


def test_castable():
    Point2 = MuStruct('Point2', ('x', MU_INT64), ('y', MU_INT64))
    Ref2 = MuRef(Point2)
    IRef2 = MuIRef(Point2)
    UPtr2 = MuUPtr(Point2)

    Point3 = MuStruct('Point3', ('super', Point2), ('z', MU_INT64))
    Ref3 = MuRef(Point3)
    IRef3 = MuIRef(Point3)
    UPtr3 = MuUPtr(Point3)

    IRNode = MuOpaqueType("IRNode")
    OpqRef = MuOpaqueRef(IRNode)

    with pytest.raises(TypeError):
        castable(Ref2, IRef2)
    with pytest.raises(TypeError):
        castable(OpqRef, Ref2)

    assert castable(Ref2, Ref3) == 1
    assert castable(Ref3, Ref2) == -1


def test_new_newhybrid():
    Point = MuStruct("Point", ("x", MU_INT64), ("y", MU_INT64))
    PointArr5 = MuArray(Point, 5)
    String = MuHybrid("String", ("length", MU_INT64), ("chars", MU_INT8))
    IRNode = MuOpaqueType("IRNode")

    ref_p = new(Point)
    assert ref_p
    assert mutypeOf(ref_p) == MuRef(Point)
    assert isinstance(ref_p._obj, mutype._mustruct)

    ref_a = new(PointArr5)
    assert ref_a
    assert isinstance(ref_a._obj, mutype._muarray)
    assert len(ref_a._obj) == 5

    ref_s = newhybrid(String, 5)
    assert ref_s
    assert isinstance(ref_s._obj.chars, mutype._mumemarray)
    assert len(ref_s._obj.chars) == 5

    refN = new(IRNode)
    assert refN
    assert isinstance(refN, mutype._muopqref)


def test_ref():
    # Spec of what ref can do
    S = MuStruct("Point", ("x", MU_INT64), ("y", MU_INT64))
    ref_S = new(S)

    # can't store or load,
    # but can access the object via _obj attribute for internal use
    with pytest.raises(AttributeError):
        o = ref_S._load()
    with pytest.raises(AttributeError):
        ref_S._store(mu_int64(10))
    assert isinstance(ref_S._obj, mutype._mustruct)

    # can get iref from ref
    i = ref_S._getiref()
    assert isinstance(i, mutype._muiref)
    assert i._obj is ref_S._obj

    # pin & unpin
    p = ref_S._pin()
    assert ref_S._ispinned()
    assert isinstance(p, mutype._muuptr)
    assert p._obj is ref_S._obj
    ref_S._unpin()
    assert not ref_S._ispinned()
    with pytest.raises(RuntimeError):
        o = p._obj      # after unpin the derived uptr becomes invalid
    with pytest.raises(RuntimeError):
        o = p._load()   # after unpin the derived uptr becomes invalid
    with pytest.raises(RuntimeError):
        ref_S._unpin()      # can not unpin an unpinned ref


def test_iref():
    Point = MuStruct("Point", ("x", MU_INT64), ("y", MU_INT64))
    PointArr5 = MuArray(Point, 5)
    String = MuHybrid("String", ("length", MU_INT64), ("chars", MU_INT8))

    # derive iref from ref
    refP = new(Point)
    irefP = refP._getiref()

    assert isinstance(irefP.x, mutype._muiref)   # accessing an attribute gives back an iref
    assert irefP.x._obj is refP._obj.x  # the iref points to the same object

    # load & store
    x = mu_float(0.2)
    with pytest.raises(TypeError):
        irefP.x._store(x)       # can not store values of different type
    a = mu_int64(42)
    irefP.x._store(a)
    assert irefP.x._load() is a
    assert refP._obj.x is a      # store in to the iref also affects the root ref

    # array
    refA = new(PointArr5)
    irefA = refA._getiref()
    assert isinstance(irefA[0], mutype._muiref)     # accessing an array item gives back an iref
    assert irefA[0]._obj is irefA._obj._items[0]
    irefA[0]._store(irefP._obj)
    assert irefA[0]._load() is irefP._obj
    assert refA._obj[0] is irefP._obj

    # hybrid
    refS = newhybrid(String, 5)
    irefS = refS._getiref()
    with pytest.raises(TypeError):
        irefS._load()       # can not load a hybrid type
    # memarray load & store
    c = mu_int8(ord('c'))
    irefS.chars[0]._store(c)
    assert irefS.chars[0]._load() is c
    assert refS._obj.chars[0] is c
    assert len(irefS.chars) == 5

def test_globalcell():
    assert issubclass(MuGlobalCell, MuIRef)
    assert issubclass(mutype._muglocalcell, mutype._muiref)

    Point = MuStruct("Point", ("x", MU_INT64), ("y", MU_INT64))
    RefPoint = MuRef(Point)
    G = MuGlobalCell(RefPoint)
    gcl = new(G)
    assert isinstance(gcl, mutype._muglobalcell)
    assert isinstance(gcl._obj, mutype._muref)
    assert not gcl._obj     # default is NULL

    refP = new(Point)
    gcl._store(refP)
    assert gcl._load() is refP

    String = MuHybrid("String", ("length", MU_INT64), ("chars", MU_INT8))
    with pytest.raises(TypeError):
        MuGlobalCell(String)        # global cell can only contain fixed sized things


def test_uptr():
    Point = MuStruct("Point", ("x", MU_INT64), ("y", MU_INT64))
    PointArr5 = MuArray(Point, 5)
    String = MuHybrid("String", ("length", MU_INT64), ("chars", MU_INT8))

    # derive uptr from ref using pinning
    refP = new(Point)
    ptrP = refP._pin()
    assert isinstance(ptrP.x, mutype._muuptr)
    # load & store
    x = mu_float(0.2)
    with pytest.raises(TypeError):
        ptrP.x._store(x)  # can not store values of different type
    a = mu_int64(42)
    ptrP.x._store(a)
    assert ptrP.x._load() is a
    assert refP._obj.x is a

    # array
    refA = new(PointArr5)
    ptrA = refA._pin()
    assert isinstance(ptrA[0], mutype._muuptr)  # accessing an array item gives back an iref
    assert ptrA[0]._obj is ptrA._obj._items[0]
    ptrA[0]._store(ptrP._obj)
    assert ptrA[0]._load() is ptrP._obj
    refA._obj[0] is ptrP._obj

    # hybrid
    refS = newhybrid(String, 5)
    ptrS = refS._pin()
    with pytest.raises(TypeError):
        ptrS._load()  # can not load a hybrid type
    # memarray load & store
    c = mu_int8(ord('c'))
    ptrS.chars[0]._store(c)
    assert ptrS.chars[0]._load() is c
    assert refS._obj.chars[0] is c

    StructWithRef = MuStruct('StructRefPoint', ('point', MuRef(Point)))
    refSWR = new(StructWithRef)
    irfSWR = refSWR._getiref()
    irfSWR.point._store(refP)
    ptrSWR = refSWR._pin()
    with pytest.raises(TypeError):
        ptrSWR.point._load()    # can not load an object reference through an unsafe pointer


if __name__ == '__main__':
    test_new_newhybrid()