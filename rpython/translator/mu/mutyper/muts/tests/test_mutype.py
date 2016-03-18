from ..mutype import (
    int8_t, int64_t, double_t, char_t,
    MuStruct, _mustruct,
    MuHybrid, _muhybrid,
    MuArray, _muarray,
    MuFuncSig, MuFuncRef, _mufuncref,
    MuRef, MuIRef, _muref, _muiref
)
from ..muentity import MuName


def test_primitives():
    assert str(int8_t) == "int8_t"
    assert int8_t.mu_name == MuName("i8")
    assert int8_t.mu_constructor == "int<8>"
    assert int8_t._mu_constructor_expanded == int8_t.mu_constructor
    assert repr(int8_t) == int8_t.mu_constructor
    assert int8_t._defl() == 0


def test_structs():
    P = MuStruct('Point', ('x', double_t), ('y', double_t))
    S = MuStruct('Circle', ('radius', double_t), ('origin', P))

    assert S.radius == double_t
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
    assert s.radius == 0.0
    s.radius = 2.0
    assert s.radius == 2.0
    s.origin.x = 5.0
    assert s.origin.x == 5.0


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

    h = _muhybrid(H, 3)
    h.length = 3
    assert h.length == 3
    assert h.chars == [0] * 3
    h.chars[0] = ord('a')
    assert h.chars[0] == ord('a')


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
    assert a.items == [0] * 10
    assert len(a) == 10
    a[9] = 1234
    assert a[9] == 1234


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
    assert str(IR) == "~ %s" % S
    assert repr(IR.mu_name) == "@irfsttCircle"
    assert IR.mu_constructor == "iref<@sttCircle>"
    assert IR._mu_constructor_expanded == "iref<%s>" % S._mu_constructor_expanded

    IR2 = MuIRef(S)
    assert IR == IR2
    assert hash(IR) == hash(IR2)

    s = _mustruct(S)
    s.radius = 2.0
    s.origin.x = 5.0
    s.origin.y = 6.0

    r = _muref(R, s)
    ir = _muiref(IR, s, r, None)

    assert r._getiref() == ir
    assert ir.radius == _muiref(MuIRef(double_t), 2.0, ir, 'radius')
    assert ir.origin == _muiref(MuIRef(P), s.origin, ir, 'origin')
    ir.origin.x._store(0.0)
    assert ir.origin.x._obj == 0.0
