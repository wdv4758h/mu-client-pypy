from rpython.translator.mu.mutyper.muts.mutype import (
    int8_t, int64_t, float_t, char_t,
    MuStruct, _mustruct,
    MuHybrid, _muhybrid,
    MuArray, _muarray
)
from rpython.translator.mu.mutyper.muts.muentity import MuName


def test_int():
    assert int8_t.mu_name == MuName("i8")
    assert int8_t.mu_constructor == "int<8>"
    assert int8_t._defl() == 0


def test_structs():
    P = MuStruct('Point', ('x', float_t), ('y', float_t))
    S = MuStruct('Circle', ('radius', float_t), ('origin', P))

    assert S.radius == float_t
    assert S.origin == P

    assert S.mu_constructor == "struct<%s %s>" % (repr(float_t.mu_name), repr(P.mu_name))
    assert S._mu_constructor_expanded == "struct<float struct<float float>>"

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

    assert H.mu_constructor == "hybrid<%s %s %s>" % (int64_t.mu_name, int64_t.mu_name, int8_t.mu_name)
    assert H._mu_constructor_expanded == "hybrid<int<64> int<64> int<8>>"

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

    assert A.mu_constructor == "array<%s %d>" % (int64_t.mu_name, 10)
    assert A._mu_constructor_expanded == "array<int<64> 10>"

    A._container_example()

    a = _muarray(A)
    assert a.items == [0] * 10
    a.setitem(9, 1234)
    assert a.getitem(9) == 1234
