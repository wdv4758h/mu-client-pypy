from rpython.translator.mu.layout import *

def test_sizeof_prim():
    assert mu_sizeOf(MU_INT8) == 1
    assert mu_sizeOf(MU_INT16) == 2
    assert mu_sizeOf(MU_INT32) == 4
    assert mu_sizeOf(MU_INT64) == 8
    assert mu_sizeOf(MU_FLOAT) == 4
    assert mu_sizeOf(MU_DOUBLE) == 8
    assert mu_sizeOf(MuRef(MU_VOID)) == 8
    assert mu_sizeOf(MuIRef(MU_VOID)) == 16
    assert mu_sizeOf(MuWeakRef(MU_VOID)) == 8
    assert mu_sizeOf(MU_VOID) == 0
    assert mu_sizeOf(MuFuncRef(MuFuncSig([], []))) == 8
    assert mu_sizeOf(MuOpaqueRef("Thread")) == 8

def test_alignof_prim():
    assert mu_alignOf(MU_INT8) == 1
    assert mu_alignOf(MU_INT16) == 2
    assert mu_alignOf(MU_INT32) == 4
    assert mu_alignOf(MU_INT64) == 8
    assert mu_alignOf(MU_FLOAT) == 4
    assert mu_alignOf(MU_DOUBLE) == 8
    assert mu_alignOf(MuRef(MU_VOID)) == 8
    assert mu_alignOf(MuIRef(MU_VOID)) == 16
    assert mu_alignOf(MuWeakRef(MU_VOID)) == 8
    assert mu_alignOf(MU_VOID) == 1
    assert mu_alignOf(MuFuncRef(MuFuncSig([], []))) == 8
    assert mu_alignOf(MuOpaqueRef("Thread")) == 8

def test_struct():
    S1 = MuStruct("stt", ('a', MU_INT8), ('b', MU_INT16), ('c', MU_INT32), ('d', MU_INT64))
    assert mu_sizeOf(S1) == 16
    assert mu_alignOf(S1) == 8

    S2 = MuStruct("stt2", ('x', MU_INT16), ('y', S1), ('z', MU_INT32))
    assert mu_sizeOf(S2) == 28
    assert mu_alignOf(S2) == 8

def test_array():
    A = MuArray(MU_INT64, 100)
    assert mu_sizeOf(A) == 800
    assert mu_alignOf(A) == 8

def test_struct_field_offset():
    S = MuStruct("stt", ('a', MU_INT8), ('b', MU_INT16), ('c', MU_INT32), ('d', MU_INT64))
    assert mu_offsetOf(S, 'a') == 0
    assert mu_offsetOf(S, 'b') == 2
    assert mu_offsetOf(S, 'c') == 4
    assert mu_offsetOf(S, 'd') == 8

def test_array_item_offset():
    A = MuArray(MU_INT64, 100)
    assert mu_offsetOf(A, 0) == 0
    assert mu_offsetOf(A, 50) == 400

def test_hybrid():
    H = MuHybrid("hyb", ('a', MU_INT8), ('b', MU_INT16), ('c', MU_INT32), ('d', MU_INT64), ('e', MU_DOUBLE))
    assert mu_hybsizeOf(H, 10) == 96
    assert mu_hybalignOf(H, 10) == 8
    assert mu_offsetOf(H, 'a') == 0
    assert mu_offsetOf(H, 'b') == 2
    assert mu_offsetOf(H, 'c') == 4
    assert mu_offsetOf(H, 'd') == 8
    assert mu_offsetOf(H, 'e') == 16

def test_hybrid_var_only():
    H = MuHybrid("hyb", ('f', MU_FLOAT))
    assert mu_hybsizeOf(H, 10) == 40
    assert mu_hybalignOf(H, 10) == 4
    assert mu_offsetOf(H, 'f') == 0