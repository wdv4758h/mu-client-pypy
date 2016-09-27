import pytest
from rpython.translator.mu.mutype import *


def test_primitives():
    assert MU_INT1.BITS == 1
    assert MU_INT128.BITS == 128
    true = mu_int1(1)
    false = mu_int1(0)
    assert true
    assert not false

    a = mu_int128(0x1234567890ABCD1234567890ABCDEF)
    assert a.get_uint64s() == \
           map(MU_INT64.get_value_type(), [0x1234567890ABCDEF, 0x1234567890ABCD])

    x = mu_int64(3)
    y = mu_int64(4)
    assert x + y == 7   # can add, can compare with python value
    assert type(x + 4) is mu_int64

    assert x != mu_int8(8)  # type equality included

    m = mu_int64(256)
    assert mu_int8(m) == mu_int8(0)     # wrap around 'cast'


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
