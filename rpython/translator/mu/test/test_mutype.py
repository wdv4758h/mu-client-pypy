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

    IRNodeRef = MuReferenceType(IRNode)     # opaque reference type
    assert IRNodeRef._val_type is mutype._mugeneral_reference

    refnode = IRNodeRef._allocate()
    assert not refnode  # NULL reference, (__nonzero__ method)
    assert mutypeOf(refnode) == IRNodeRef   # has _TYPE

    node = IRNode._example()
    refnode._obj = node     # set reference to an opaque object
    assert refnode._obj is node
    assert refnode  # not NULL


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
    OpqRef = MuReferenceType(IRNode)

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

    ref_p = new(Point)
    assert ref_p
    assert mutypeOf(ref_p) == MuRef(Point)
    iref_p = ref_p._getiref()
    assert iref_p._obj is ref_p._obj
    assert isinstance(iref_p.x, mutype._muiref)
    assert mutypeOf(iref_p.x) == MuIRef(MU_INT64)

    ref_a = new(PointArr5)
    iref_a = ref_a._getiref()
    assert ref_a
    assert isinstance(iref_a._obj, mutype._muarray)
    assert len(iref_a) == 5

    ref_s = newhybrid(String, 5)
    iref_s = ref_s._getiref()
    assert isinstance(iref_s.chars._obj, mutype._mumemarray)


def test_ref():
    S = MuStruct("Point", ("x", MU_INT64), ("y", MU_INT64))

    r = new(S)
    RefS = MuRef(S)
    print RefS
    assert RefS.TO is S


def test_store():
    Point = MuStruct("Point", ("x", MU_INT64), ("y", MU_INT64))
    r = new(Point)
    i = r._getiref()
    p = r._pin()

    i.x._store(mu_int64(10))
    assert i.x._obj == i.x._load() == mu_int64(10)
    assert p.x._obj == p.x._load() == mu_int64(10)

    String = MuHybrid("String", ("length", MU_INT64), ("chars", MU_INT8))
    ref_s = newhybrid(String, 5)
    iref_s = ref_s._getiref()
    iref_s.chars[0] = mu_int8(ord('c'))
    assert iref_s.chars[0] == mu_int8(ord('c'))

    PointArr5 = MuArray(Point, 5)
    ref_a = new(PointArr5)
    iref_a = ref_a._getiref()
    iref_a[0].x._store(mu_int64(20))
    assert iref_a[0].x._obj == iref_a[0].x._load() == mu_int64(20)


def test_pinning():
    S = MuStruct("Point", ("x", MU_INT64), ("y", MU_INT64))
    r = new(S)
    p = r._pin()

    assert isinstance(p, mutype._muuptr)
    assert p._obj is r._obj
    assert r._ispinned()

    r._unpin()
    assert not r._ispinned()

    with pytest.raises(RuntimeError):
        p.x  # after unpin, the derived pointer becomes invalid

if __name__ == '__main__':
    test_new_newhybrid()