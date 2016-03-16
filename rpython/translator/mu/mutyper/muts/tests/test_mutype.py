from ..mutype import (
    int8_t, int64_t, float_t, char_t,
    MuStruct, _mustruct,
    MuHybrid, _muhybrid,
    MuArray, _muarray,
    MuFuncRef, MuFuncSig
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
    P = MuStruct('Point', ('x', float_t), ('y', float_t))
    S = MuStruct('Circle', ('radius', float_t), ('origin', P))

    assert S.radius == float_t
    assert S.origin == P

    assert S.mu_name == MuName("sttCircle")
    assert str(S) == "MuStruct Circle { radius, origin }"
    assert S.mu_constructor == "struct<%s %s>" % (repr(float_t.mu_name), repr(P.mu_name))
    assert S._mu_constructor_expanded == "struct<float struct<float float>>"
    assert repr(S) == S._mu_constructor_expanded

    S2 = MuStruct('Circle', ('radius', float_t), ('origin', P))
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
    a.setitem(9, 1234)
    assert a.getitem(9) == 1234


def test_funcsig():
    Sig = MuFuncSig((int64_t, float_t), (MuStruct("packed", ('i', int64_t), ('f', float_t)),))

    assert str(Sig) == "( int64_t, float_t ) -> MuStruct packed { i, f }"
    assert Sig.mu_constructor == "(@i64, @flt) -> @sttpacked"
    assert Sig._mu_constructor_expanded == "( int<64>, float ) -> struct<int<64> float>"
    assert repr(Sig.mu_name) == "@sig_i64flt_sttpacked"


def test_funcref():
    Sig = MuFuncSig((float_t, float_t), (float_t,))
    assert repr(Sig.mu_name) == "@sig_fltflt_flt"

    R = MuFuncRef(Sig)
    assert str(R) == "MuFuncRef ( float_t, float_t ) -> float_t"
    assert repr(R.mu_name) == "@fnrsig_fltflt_flt"
    assert R.mu_constructor == "funcref<@sig_fltflt_flt>"
    assert R._mu_constructor_expanded == "funcref<( float, float ) -> float>"
