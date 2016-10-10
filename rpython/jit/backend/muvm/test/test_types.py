""" Tests for MuVM types 
"""

import py

from rpython.jit.backend.muvm.test.support import JitMuMixin
from rpython.jit.metainterp.history import  (INT, FLOAT, VOID,
                                            STRUCT, REF, VECTOR)
from rpython.jit.backend.muvm.mutypes import (MuType, MuIntType, MuFloatType,
                                                MuDoubleType, MuVoidType,
                                                MuStructType, MuRefType,
                                                MuVectorType, MuIRefType,
                                                MuWeakRefType, MuHybridType,
                                                MuArrayType, MuFuncRefType,
                                                MuThreadRefType, MuStackRefType,
                                                MuFrameCursorRefType,
                                                MuTagRef64Type, MuPtrType,
                                                MuFuncPtrType, MuFuncSig, get_type,
                                                DOUBLE, IREF, WEAKREF, HYBRID,
                                                ARRAY, FUNCREF, THREADREF,
                                                FRAMECURSORREF, TAGREF64, UPTR,
                                                UFUNCPTR)

i32 = get_type(INT, 32)
i64 = get_type(INT, 64)
sig1 = MuFuncSig( [i32, i32], [i32])
sig2 = MuFuncSig( [], [] )
flt = get_type(FLOAT)
dbl = get_type(DOUBLE)
void = get_type(VOID)
ref_i32 = get_type(REF, reftype = i32)
ref_i64 = get_type(REF, reftype = i64)
vec_i32_3 = get_type(VECTOR, vectype = i32, length = 3)
vec_i64_3 = get_type(VECTOR, vectype = i64, length = 3)
iref_i32  = get_type(IREF, reftype = i32)
iref_i64  = get_type(IREF, reftype = i64)
weakref_i32 = get_type(WEAKREF, reftype = i32)
weakref_i64 = get_type(WEAKREF, reftype = i64)
hybrid1 = get_type(HYBRID, fixedtypes = [i32, i64, ref_i32], vartype = i64)
hybrid2 = get_type(HYBRID, fixedtypes = [i64, ref_i32], vartype = i64)
struct1 = get_type(STRUCT, types=[i32, i64])
struct2 = get_type(STRUCT, types=[i32, i64, i32])

def test_basic():
    assert i32 != i64
    assert i32 == get_type(INT, 32)
    assert i64 == get_type(INT, 64)
    assert flt == get_type(FLOAT)
    assert dbl == get_type(DOUBLE)
    assert flt != dbl
    assert void == get_type(VOID)
    assert void != dbl
    assert dbl  != void
    assert ref_i32 == get_type(REF, i32)
    assert ref_i32 != ref_i64
    assert ref_i64 == get_type(REF, i64)
    assert vec_i32_3 == get_type(VECTOR, vectype=i32, length=3)
    assert vec_i64_3 == get_type(VECTOR, vectype=i64, length=3)
    assert vec_i32_3 != vec_i64_3
    assert vec_i32_3 != get_type(VECTOR, vectype=i32, length = 4)
    assert sig1 == MuFuncSig( [i32, i32], [i32])
    assert sig1 != sig2
    assert str(flt)  == '@f_t'
    assert str(i32)  == '@i32_t'
    assert str(i64)  == '@i64_t'
    assert str(sig1) == '@funcsig0'
    assert str(sig2) == '@funcsig1'

