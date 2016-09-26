from rpython.translator.mu.mutype import *


def test_primitives():
    assert MU_INT1.BITS == 1
    assert MU_INT128.BITS == 128
