import pytest
from ..mutype import (
    int1_t, int8_t, int16_t, int32_t, int64_t, double_t, char_t, _muprimitive, muint_type,
    MuStruct, _mustruct,
    MuHybrid, _muhybrid,
    MuArray, _muarray,
    MuFuncSig, MuFuncRef, _mufuncref,
    MuRef, MuIRef, _muref, _muiref,
    MuUPtr, _muuptr,
    new, newhybrid
)
from ..muentity import MuName


def test_primitives():
    assert str(int8_t) == "int8_t"
    assert int8_t.mu_name == MuName("i8")
    assert int8_t.mu_constructor == "int<8>"
    assert int8_t._mu_constructor_expanded == int8_t.mu_constructor
    assert repr(int8_t) == int8_t.mu_constructor
    assert int8_t._defl() == int8_t(0)

    i = _muprimitive(int8_t, 255)
    assert i == _muprimitive(int8_t, 255)
    assert i == int8_t(255)
    assert i != _muprimitive(int64_t, 255)


def test_muint_type():
    assert muint_type(1) == int1_t
    assert muint_type(-1) == int8_t
    assert muint_type(0xFF) == int8_t
    assert muint_type(256) == int16_t


def test_structs():
    P = MuStruct('Point', ('x', double_t), ('y', double_t))
    S = MuStruct('Circle', ('radius', double_t), ('origin', P))

    assert S.radius == double_t
    assert S[0] == double_t
    assert S.origin == P

    assert S.mu_name == MuName("sttCircle")
    assert str(S) == "MuStruct Circle { radius, origin }"
    assert S.mu_constructor == "struct<%s %s>" % (repr(double_t.mu_name), repr(P.mu_name))
    assert S._mu_constructor_expanded == "struct<double struct<double double>>"
    assert repr(S) == S._mu_constructor_expanded

    S2 = MuStruct('Circle', ('radius', double_t), ('origin', P))
    assert hash(S) == hash(S2)  # equal types should have the same hash

    S._container_example()

    s = _mustruct(S)
    assert s.radius == double_t(0.0)
    with pytest.raises(TypeError):
        s.radius = 2.0
    s.radius = double_t(2.0)
    assert s.radius == double_t(2.0)
    s.origin.x = double_t(5.0)
    assert s.origin.x == double_t(5.0)


def test_hybrids():
    H = MuHybrid("String", ('hash', int64_t), ('length', int64_t), ('chars', char_t))

    assert H._varfld == 'chars'
    assert H.chars == char_t
    assert H.length == int64_t

    assert H.mu_name == MuName("hybString")
    assert str(H) == "MuHybrid String { hash, length | chars }"
    assert H.mu_constructor == "hybrid<%s %s %s>" % (int64_t.mu_name, int64_t.mu_name, int8_t.mu_name)
    assert H._mu_constructor_expanded == "hybrid<int<64> int<64> int<8>>"
    assert repr(H) == H._mu_constructor_expanded

    H2 = MuHybrid("String", ('hash', int64_t), ('length', int64_t), ('chars', char_t))
    assert hash(H) == hash(H2)

    H._container_example()
    with pytest.raises(TypeError):
        h = _muhybrid(H, 3)
    h = _muhybrid(H, int64_t(3))
    with pytest.raises(TypeError):
        h.length = 3
    h.length = int64_t(3)
    assert h.length == int64_t(3)
    assert len(h.chars) == 3
    h.chars[0] = int8_t(ord('a'))
    assert h.chars[0] == int8_t(ord('a'))


def test_arrays():
    A = MuArray(int64_t, 10)

    assert A.OF == int64_t
    assert A.length == 10

    assert A.mu_name == MuName("arr10i64")
    assert str(A) == "MuArray of %d %s" % (10, "int64_t")
    assert A.mu_constructor == "array<%s %d>" % (int64_t.mu_name, 10)
    assert A._mu_constructor_expanded == "array<int<64> 10>"
    assert repr(A) == A._mu_constructor_expanded

    A2 = MuArray(int64_t, 10)
    assert hash(A) == hash(A2)

    A._container_example()

    a = _muarray(A)
    assert a.items == [int64_t(0)] * 10
    assert len(a) == 10
    with pytest.raises(TypeError):
        a[9] = 1234
    a[9] = int64_t(1234)
    assert a[9] == int64_t(1234)


def test_funcsig():
    Sig = MuFuncSig((int64_t, double_t), (MuStruct("packed", ('i', int64_t), ('f', double_t)),))

    assert str(Sig) == "( int64_t, double_t ) -> MuStruct packed { i, f }"
    assert Sig.mu_constructor == "(@i64, @dbl) -> @sttpacked"
    assert Sig._mu_constructor_expanded == "( int<64>, double ) -> struct<int<64> double>"
    assert repr(Sig.mu_name) == "@sig_i64dbl_sttpacked"

    Sig2 = MuFuncSig((int64_t, double_t), (MuStruct("packed", ('i', int64_t), ('f', double_t)),))

    assert Sig == Sig2
    assert hash(Sig) == hash(Sig2)


def test_funcref():
    Sig = MuFuncSig((double_t, double_t), (double_t,))
    assert repr(Sig.mu_name) == "@sig_dbldbl_dbl"

    R = MuFuncRef(Sig)
    assert str(R) == "MuFuncRef ( double_t, double_t ) -> double_t"
    assert repr(R.mu_name) == "@fnrsig_dbldbl_dbl"
    assert R.mu_constructor == "funcref<@sig_dbldbl_dbl>"
    assert R._mu_constructor_expanded == "funcref<( double, double ) -> double>"

    R2 = MuFuncRef(Sig)

    assert R == R2
    assert hash(R) == hash(R2)


def test_refs():
    P = MuStruct('Point', ('x', double_t), ('y', double_t))
    S = MuStruct('Circle', ('radius', double_t), ('origin', P))
    R = MuRef(S)

    assert str(R) == "@ %s" % S
    assert repr(R.mu_name) == "@refsttCircle"
    assert R.mu_constructor == "ref<@sttCircle>"
    assert R._mu_constructor_expanded == "ref<%s>" % S._mu_constructor_expanded

    R2 = MuRef(S)
    assert R == R2
    assert hash(R) == hash(R2)

    IR = MuIRef(S)
    assert str(IR) == "& %s" % S
    assert repr(IR.mu_name) == "@irfsttCircle"
    assert IR.mu_constructor == "iref<@sttCircle>"
    assert IR._mu_constructor_expanded == "iref<%s>" % S._mu_constructor_expanded

    IR2 = MuIRef(S)
    assert IR == IR2
    assert hash(IR) == hash(IR2)

    s = _mustruct(S)
    s.radius = double_t(2.0)
    s.origin.x = double_t(5.0)
    s.origin.y = double_t(6.0)

    r = _muref(R, s)
    ir = _muiref(IR, s, r, None)

    # getattr will return iref.
    # to access the referenced object, use _load/_store or ._obj
    assert r._getiref() == ir
    assert ir.radius == _muiref(MuIRef(double_t), double_t(2.0), ir._obj, 'radius')
    assert hash(ir.radius) == hash(_muiref(MuIRef(double_t), double_t(2.0), ir._obj, 'radius'))
    assert ir.origin == _muiref(MuIRef(P), s.origin, ir._obj, 'origin')
    with pytest.raises(AttributeError):
        ir.origin.x = double_t(0.0)
    with pytest.raises(TypeError):
        ir.origin.x._store(0.0)
    ir.origin.x._store(double_t(0.0))
    assert ir.origin.x._obj == double_t(0.0)

    A = MuArray(int64_t, 5)
    a = _muarray(A)
    ra = _muref(MuRef(A), a)
    ira = ra._obj
    assert ira[1] == (ira[0] + 1)   # GETELEMIREF, SHIFTIREF
    with pytest.raises(AttributeError):
        ira[0] = int64_t(1)
    ira[0]._obj = int64_t(1)             # explicit load/store
    ira[1]._obj = int64_t(2)
    assert ira[0]._obj == int64_t(1)
    assert ira[1]._obj == int64_t(2)

    H = MuHybrid('string', ('length', int64_t), ('chars', char_t))
    with pytest.raises(TypeError):
        h = _muhybrid(H, 3)
    h = _muhybrid(H, int64_t(3))
    rh = _muref(MuRef(H), h)
    irh = rh._obj
    irh.length._obj = int64_t(3)
    assert irh.chars[0] == irh.chars
    assert irh.chars[1] == (irh.chars + 1)
    irh.chars._obj = int8_t(ord('G'))
    assert irh.chars[0]._obj == int8_t(ord('G'))
    irh.chars[1]._obj = int8_t(ord('o'))
    assert irh.chars[1]._obj == int8_t(ord('o'))

    pa = ra._pin()
    assert pa == _muuptr(MuUPtr(A), a, ra, None)
    assert pa == ira._pin()
    assert isinstance(pa[0], _muuptr)
    ph = rh._pin()
    assert isinstance(ph.length, _muuptr)
    assert isinstance(ph.chars, _muuptr)
    ph.chars[1]._obj = int8_t(ord('o'))
    assert ph.chars[1]._obj == int8_t(ord('o'))


def test_memalloc():
    A = MuArray(int64_t, 5)
    ra = new(A)
    assert isinstance(ra, _muref)
    assert ra._T == A

    ri = new(int64_t)
    assert ri._T == int64_t

    H = MuHybrid('string', ('length', int64_t), ('chars', char_t))
    with pytest.raises(TypeError):
        new(H)
    rh = newhybrid(H, int64_t(10))
    assert rh._getiref().chars._obj == int8_t(0)

