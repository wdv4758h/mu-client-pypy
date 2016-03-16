from ..mutype import *
from ..muentity import MuName


def test_int():
    assert int8_t.bits == 8
    assert int8_t.mu_name == MuName("i8")
    assert int8_t.mu_constructor == "int<8>"
    assert int8_t._defl() == 0
