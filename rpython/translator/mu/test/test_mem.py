from rpython.mutyper.muts.mutype import *
from ..mem import *


def test_sizeOf():
    A = MuArray(int8_t, 3)
    assert mu_sizeOf(A) == 3

    PA = MuRef(A)
    assert mu_sizeOf(PA) == 8

    S = MuStruct("test", ('arr', A), ('n', int64_t))
    assert mu_sizeOf(S) == 16

    EX = MuStruct("MixedData", ('data1', char_t), ('data2', int16_t), ('data3', int32_t), ('data4', char_t))
    assert mu_sizeOf(EX) == 12

    assert mu_sizeOf(MuStruct('empty')) == 0


def test_offsetOf():
    S = MuStruct("test", ('a', int8_t), ('b', int16_t), ('c', int32_t), ('d', int64_t))
    assert mu_offsetOf(S, 'a') == 0
    assert mu_offsetOf(S, 'b') == 2
    assert mu_offsetOf(S, 'c') == 4
    assert mu_offsetOf(S, 'd') == 8
