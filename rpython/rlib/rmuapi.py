"""
Mu API RPython binding.
"""
from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype
from rpython.translator.tool.cbuild import ExternalCompilationInfo
import os

mu_dir = os.path.join(os.getenv('MU'), 'cbinding')
eci = ExternalCompilationInfo(includes=['refimpl2-start.h', 'muapi.h'],
                              include_dirs=[mu_dir],
                              libraries=['murefimpl2start'],
                              library_dirs=[mu_dir])

_fnp = rffi.CCallback
# -------------------------------------------------------------------------------------------------------
# Types
MuValue = rffi.VOIDP
MuValuePtr = rffi.VOIDPP
MuID = rffi.UINT        # uint32_t
MuIDPtr = rffi.UINTP
MuName = rffi.CCHARP
MuNamePtr = rffi.CCHARPP
MuCPtr = rffi.VOIDP
MuCPtrPtr = rffi.VOIDPP
MuCFP = _fnp([], lltype.Void)
MuCFPPtr = rffi.CArray(MuCFP)
MuBool = rffi.INT
MuBoolPtr = rffi.INTP
MuArraySize = rffi.UINTPTR_T
MuArraySizePtr = rffi.UINTPTR_TP
MuWPID = rffi.UINT
MuWPIDPtr = rffi.UINTP
MuFlag = rffi.UINT
MuFlagPtr = rffi.UINTP
MuValuesFreer = _fnp([MuValuePtr, MuCPtr], lltype.Void)

MuSeqValue = MuValue
MuGenRefValue = MuValue

MuIntValue = MuValue
MuFloatValue = MuValue
MuDoubleValue = MuValue
MuUPtrValue = MuValue
MuUFPValue = MuValue

MuStructValue = MuSeqValue
MuArrayValue = MuSeqValue
MuVectorValue = MuSeqValue

MuRefValue = MuGenRefValue
MuIRefValue = MuGenRefValue
MuTagRef64Value = MuGenRefValue
MuFuncRefValue = MuGenRefValue
MuThreadRefValue = MuGenRefValue
MuStackRefValue = MuGenRefValue
MuFCRefValue = MuGenRefValue
MuIRNodeRefValue = MuGenRefValue


MuIRNode = MuIRNodeRefValue
MuBundleNode = MuIRNode
MuChildNode = MuIRNode
MuTypeNode = MuChildNode
MuFuncSigNode = MuChildNode
MuVarNode = MuChildNode
MuGlobalVarNode = MuVarNode
MuConstNode = MuGlobalVarNode
MuGlobalNode = MuGlobalVarNode 
MuFuncNode = MuGlobalVarNode
MuExpFuncNode = MuGlobalVarNode
MuLocalVarNode = MuVarNode
MuNorParamNode = MuLocalVarNode
MuExcParamNode = MuLocalVarNode
MuInstResNode = MuLocalVarNode 
MuFuncVerNode = MuChildNode
MuBBNode = MuChildNode
MuInstNode = MuChildNode

MuIRNodePtr = rffi.CArray(MuIRNode)
MuBundleNodePtr = rffi.CArray(MuBundleNode)
MuChildNodePtr = rffi.CArray(MuChildNode)
MuTypeNodePtr = rffi.CArray(MuTypeNode)
MuFuncSigNodePtr = rffi.CArray(MuFuncSigNode)
MuVarNodePtr = rffi.CArray(MuVarNode)
MuGlobalVarNodePtr = rffi.CArray(MuGlobalVarNode)
MuConstNodePtr = rffi.CArray(MuConstNode)
MuGlobalNodePtr = rffi.CArray(MuGlobalNode)
MuFuncNodePtr = rffi.CArray(MuFuncNode)
MuExpFuncNodePtr = rffi.CArray(MuExpFuncNode)
MuLocalVarNodePtr = rffi.CArray(MuLocalVarNode)
MuNorParamNodePtr = rffi.CArray(MuNorParamNode)
MuExcParamNodePtr = rffi.CArray(MuExcParamNode)
MuInstResNodePtr = rffi.CArray(MuInstResNode)
MuFuncVerNodePtr = rffi.CArray(MuFuncVerNode)
MuBBNodePtr = rffi.CArray(MuBBNode)
MuInstNodePtr = rffi.CArray(MuInstNode)

MuTrapHandlerResult = MuFlag
MuTrapHandlerResultPtr = rffi.CArray(MuTrapHandlerResult)
MuStackRefValuePtr = rffi.CArray(MuStackRefValue)
MuValuesFreerPtr = rffi.CArray(MuValuesFreer)
MuRefValuePtr = rffi.CArray(MuRefValue)

# --------------------------------
# Flags
class MuTrapHandlerResult:
    _lltype = MuFlag
    THREAD_EXIT = 0x00
    REBIND_PASS_VALUES = 0x01
    REBIND_THROW_EXC = 0x02
class MuDestKind:
    _lltype = MuFlag
    NORMAL = 0x01
    EXCEPT = 0x02
    TRUE = 0x03
    FALSE = 0x04
    DEFAULT = 0x05
    DISABLED = 0x06
    ENABLED = 0x07
class MuBinOptr:
    _lltype = MuFlag
    ADD = 0x01
    SUB = 0x02
    MUL = 0x03
    SDIV = 0x04
    SREM = 0x05
    UDIV = 0x06
    UREM = 0x07
    SHL = 0x08
    LSHR = 0x09
    ASHR = 0x0A
    AND = 0x0B
    OR = 0x0C
    XOR = 0x0D
    FADD = 0xB0
    FSUB = 0xB1
    FMUL = 0xB2
    FDIV = 0xB3
    FREM = 0xB4
class MuCmpOptr:
    _lltype = MuFlag
    EQ = 0x20
    NE = 0x21
    SGE = 0x22
    SGT = 0x23
    SLE = 0x24
    SLT = 0x25
    UGE = 0x26
    UGT = 0x27
    ULE = 0x28
    ULT = 0x29
    FFALSE = 0xC0
    FTRUE = 0xC1
    FUNO = 0xC2
    FUEQ = 0xC3
    FUNE = 0xC4
    FUGT = 0xC5
    FUGE = 0xC6
    FULT = 0xC7
    FULE = 0xC8
    FORD = 0xC9
    FOEQ = 0xCA
    FONE = 0xCB
    FOGT = 0xCC
    FOGE = 0xCD
    FOLT = 0xCE
    FOLE = 0xCF
class MuConvOptr:
    _lltype = MuFlag
    TRUNC = 0x30
    ZEXT = 0x31
    SEXT = 0x32
    FPTRUNC = 0x33
    FPEXT = 0x34
    FPTOUI = 0x35
    FPTOSI = 0x36
    UITOFP = 0x37
    SITOFP = 0x38
    BITCAST = 0x39
    REFCAST = 0x3A
    PTRCAST = 0x3B
class MuMemOrd:
    _lltype = MuFlag
    NOT_ATOMIC = 0x00
    RELAXED = 0x01
    CONSUME = 0x02
    ACQUIRE = 0x03
    RELEASE = 0x04
    ACQ_REL = 0x05
    SEQ_CST = 0x06
class MuAtomicRMWOptr:
    _lltype = MuFlag
    XCHG = 0x00
    ADD = 0x01
    SUB = 0x02
    AND = 0x03
    NAND = 0x04
    OR = 0x05
    XOR = 0x06
    MAX = 0x07
    MIN = 0x08
    UMAX = 0x09
    UMIN = 0x0A
class MuCallConv:
    _lltype = MuFlag
    DEFAULT = 0x00
class MuCommInst:
    _lltype = MuFlag
    UVM_NEW_STACK = 0x201
    UVM_KILL_STACK = 0x202
    UVM_THREAD_EXIT = 0x203
    UVM_CURRENT_STACK = 0x204
    UVM_SET_THREADLOCAL = 0x205
    UVM_GET_THREADLOCAL = 0x206
    UVM_TR64_IS_FP = 0x211
    UVM_TR64_IS_INT = 0x212
    UVM_TR64_IS_REF = 0x213
    UVM_TR64_FROM_FP = 0x214
    UVM_TR64_FROM_INT = 0x215
    UVM_TR64_FROM_REF = 0x216
    UVM_TR64_TO_FP = 0x217
    UVM_TR64_TO_INT = 0x218
    UVM_TR64_TO_REF = 0x219
    UVM_TR64_TO_TAG = 0x21a
    UVM_FUTEX_WAIT = 0x220
    UVM_FUTEX_WAIT_TIMEOUT = 0x221
    UVM_FUTEX_WAKE = 0x222
    UVM_FUTEX_CMP_REQUEUE = 0x223
    UVM_KILL_DEPENDENCY = 0x230
    UVM_NATIVE_PIN = 0x240
    UVM_NATIVE_UNPIN = 0x241
    UVM_NATIVE_EXPOSE = 0x242
    UVM_NATIVE_UNEXPOSE = 0x243
    UVM_NATIVE_GET_COOKIE = 0x244
    UVM_META_ID_OF = 0x250
    UVM_META_NAME_OF = 0x251
    UVM_META_LOAD_BUNDLE = 0x252
    UVM_META_LOAD_HAIL = 0x253
    UVM_META_NEW_CURSOR = 0x254
    UVM_META_NEXT_FRAME = 0x255
    UVM_META_COPY_CURSOR = 0x256
    UVM_META_CLOSE_CURSOR = 0x257
    UVM_META_CUR_FUNC = 0x258
    UVM_META_CUR_FUNC_VER = 0x259
    UVM_META_CUR_INST = 0x25a
    UVM_META_DUMP_KEEPALIVES = 0x25b
    UVM_META_POP_FRAMES_TO = 0x25c
    UVM_META_PUSH_FRAME = 0x25d
    UVM_META_ENABLE_WATCHPOINT = 0x25e
    UVM_META_DISABLE_WATCHPOINT = 0x25f
    UVM_META_SET_TRAP_HANDLER = 0x260
    UVM_IRBUILDER_NEW_BUNDLE = 0x300
    UVM_IRBUILDER_LOAD_BUNDLE_FROM_NODE = 0x301
    UVM_IRBUILDER_ABORT_BUNDLE_NODE = 0x302
    UVM_IRBUILDER_GET_NODE = 0x303
    UVM_IRBUILDER_GET_ID = 0x304
    UVM_IRBUILDER_SET_NAME = 0x305
    UVM_IRBUILDER_NEW_TYPE_INT = 0x306
    UVM_IRBUILDER_NEW_TYPE_FLOAT = 0x307
    UVM_IRBUILDER_NEW_TYPE_DOUBLE = 0x308
    UVM_IRBUILDER_NEW_TYPE_UPTR = 0x309
    UVM_IRBUILDER_SET_TYPE_UPTR = 0x30a
    UVM_IRBUILDER_NEW_TYPE_UFUNCPTR = 0x30b
    UVM_IRBUILDER_SET_TYPE_UFUNCPTR = 0x30c
    UVM_IRBUILDER_NEW_TYPE_STRUCT = 0x30d
    UVM_IRBUILDER_NEW_TYPE_HYBRID = 0x30e
    UVM_IRBUILDER_NEW_TYPE_ARRAY = 0x30f
    UVM_IRBUILDER_NEW_TYPE_VECTOR = 0x310
    UVM_IRBUILDER_NEW_TYPE_VOID = 0x311
    UVM_IRBUILDER_NEW_TYPE_REF = 0x312
    UVM_IRBUILDER_SET_TYPE_REF = 0x313
    UVM_IRBUILDER_NEW_TYPE_IREF = 0x314
    UVM_IRBUILDER_SET_TYPE_IREF = 0x315
    UVM_IRBUILDER_NEW_TYPE_WEAKREF = 0x316
    UVM_IRBUILDER_SET_TYPE_WEAKREF = 0x317
    UVM_IRBUILDER_NEW_TYPE_FUNCREF = 0x318
    UVM_IRBUILDER_SET_TYPE_FUNCREF = 0x319
    UVM_IRBUILDER_NEW_TYPE_TAGREF64 = 0x31a
    UVM_IRBUILDER_NEW_TYPE_THREADREF = 0x31b
    UVM_IRBUILDER_NEW_TYPE_STACKREF = 0x31c
    UVM_IRBUILDER_NEW_TYPE_FRAMECURSORREF = 0x31d
    UVM_IRBUILDER_NEW_TYPE_IRNODEREF = 0x31e
    UVM_IRBUILDER_NEW_FUNCSIG = 0x31f
    UVM_IRBUILDER_NEW_CONST_INT = 0x320
    UVM_IRBUILDER_NEW_CONST_INT_EX = 0x321
    UVM_IRBUILDER_NEW_CONST_FLOAT = 0x322
    UVM_IRBUILDER_NEW_CONST_DOUBLE = 0x323
    UVM_IRBUILDER_NEW_CONST_NULL = 0x324
    UVM_IRBUILDER_NEW_CONST_SEQ = 0x325
    UVM_IRBUILDER_NEW_GLOBAL_CELL = 0x326
    UVM_IRBUILDER_NEW_FUNC = 0x327
    UVM_IRBUILDER_NEW_FUNC_VER = 0x328
    UVM_IRBUILDER_NEW_EXP_FUNC = 0x329
    UVM_IRBUILDER_NEW_BB = 0x32a
    UVM_IRBUILDER_NEW_NOR_PARAM = 0x32b
    UVM_IRBUILDER_NEW_EXC_PARAM = 0x32c
    UVM_IRBUILDER_NEW_INST_RES = 0x32d
    UVM_IRBUILDER_ADD_DEST = 0x32e
    UVM_IRBUILDER_ADD_KEEPALIVES = 0x32f
    UVM_IRBUILDER_NEW_BINOP = 0x330
    UVM_IRBUILDER_NEW_CMP = 0x331
    UVM_IRBUILDER_NEW_CONV = 0x332
    UVM_IRBUILDER_NEW_SELECT = 0x333
    UVM_IRBUILDER_NEW_BRANCH = 0x334
    UVM_IRBUILDER_NEW_BRANCH2 = 0x335
    UVM_IRBUILDER_NEW_SWITCH = 0x336
    UVM_IRBUILDER_ADD_SWITCH_DEST = 0x337
    UVM_IRBUILDER_NEW_CALL = 0x338
    UVM_IRBUILDER_NEW_TAILCALL = 0x339
    UVM_IRBUILDER_NEW_RET = 0x33a
    UVM_IRBUILDER_NEW_THROW = 0x33b
    UVM_IRBUILDER_NEW_EXTRACTVALUE = 0x33c
    UVM_IRBUILDER_NEW_INSERTVALUE = 0x33d
    UVM_IRBUILDER_NEW_EXTRACTELEMENT = 0x33e
    UVM_IRBUILDER_NEW_INSERTELEMENT = 0x33f
    UVM_IRBUILDER_NEW_SHUFFLEVECTOR = 0x340
    UVM_IRBUILDER_NEW_NEW = 0x341
    UVM_IRBUILDER_NEW_NEWHYBRID = 0x342
    UVM_IRBUILDER_NEW_ALLOCA = 0x343
    UVM_IRBUILDER_NEW_ALLOCAHYBRID = 0x344
    UVM_IRBUILDER_NEW_GETIREF = 0x345
    UVM_IRBUILDER_NEW_GETFIELDIREF = 0x346
    UVM_IRBUILDER_NEW_GETELEMIREF = 0x347
    UVM_IRBUILDER_NEW_SHIFTIREF = 0x348
    UVM_IRBUILDER_NEW_GETVARPARTIREF = 0x349
    UVM_IRBUILDER_NEW_LOAD = 0x34a
    UVM_IRBUILDER_NEW_STORE = 0x34b
    UVM_IRBUILDER_NEW_CMPXCHG = 0x34c
    UVM_IRBUILDER_NEW_ATOMICRMW = 0x34d
    UVM_IRBUILDER_NEW_FENCE = 0x34e
    UVM_IRBUILDER_NEW_TRAP = 0x34f
    UVM_IRBUILDER_NEW_WATCHPOINT = 0x350
    UVM_IRBUILDER_NEW_WPBRANCH = 0x351
    UVM_IRBUILDER_NEW_CCALL = 0x352
    UVM_IRBUILDER_NEW_NEWTHREAD = 0x353
    UVM_IRBUILDER_NEW_SWAPSTACK_RET = 0x354
    UVM_IRBUILDER_NEW_SWAPSTACK_KILL = 0x355
    UVM_IRBUILDER_SET_NEWSTACK_PASS_VALUES = 0x356
    UVM_IRBUILDER_SET_NEWSTACK_THROW_EXC = 0x357
    UVM_IRBUILDER_NEW_COMMINST = 0x358


MuVM = lltype.ForwardReference()
MuCtx = lltype.ForwardReference()
MuVMPtr = lltype.Ptr(MuVM)
MuCtxPtr = lltype.Ptr(MuCtx)

MuTrapHandler = _fnp([
    MuCtxPtr, MuThreadRefValue, MuStackRefValue, MuWPID,   # input
    MuTrapHandlerResultPtr, MuStackRefValuePtr, rffi.CArray(MuValuePtr), MuArraySizePtr, 
    MuValuesFreerPtr, MuCPtrPtr, MuRefValuePtr,             # output
    MuCPtr  #input
], lltype.Void)

MuVM.become(rffi.CStruct(
    'MuVM',
    ('header', rffi.VOIDP),
    ('new_context', _fnp([MuVMPtr], MuCtxPtr)),
    ('id_of', _fnp([MuVMPtr, MuName], MuID)),
    ('name_of', _fnp([MuVMPtr, MuID], MuName)),
    ('set_trap_handler', _fnp([MuVMPtr, MuTrapHandler, MuCPtr], lltype.Void)),
    ('execute', _fnp([MuVMPtr], lltype.Void)),
    ('get_mu_error_ptr', _fnp([MuVMPtr], rffi.INTP))
))

MuCtx.become(rffi.CStruct(
    'MuCtx',
    ('header', rffi.VOIDP),
    ('id_of', rffi.CCallback([MuCtxPtr, MuName], MuID)),
    ('name_of', rffi.CCallback([MuCtxPtr, MuID], MuName)),
    ('close_context', rffi.CCallback([MuCtxPtr], lltype.Void)),
    ('load_bundle', rffi.CCallback([MuCtxPtr, rffi.CCHARP, MuArraySize], lltype.Void)),
    ('load_hail', rffi.CCallback([MuCtxPtr, rffi.CCHARP, MuArraySize], lltype.Void)),
    ('handle_from_sint8', rffi.CCallback([MuCtxPtr, rffi.CHAR, rffi.INT], MuIntValue)),
    ('handle_from_uint8', rffi.CCallback([MuCtxPtr, rffi.UCHAR, rffi.INT], MuIntValue)),
    ('handle_from_sint16', rffi.CCallback([MuCtxPtr, rffi.SHORT, rffi.INT], MuIntValue)),
    ('handle_from_uint16', rffi.CCallback([MuCtxPtr, rffi.USHORT, rffi.INT], MuIntValue)),
    ('handle_from_sint32', rffi.CCallback([MuCtxPtr, rffi.INT, rffi.INT], MuIntValue)),
    ('handle_from_uint32', rffi.CCallback([MuCtxPtr, rffi.UINT, rffi.INT], MuIntValue)),
    ('handle_from_sint64', rffi.CCallback([MuCtxPtr, rffi.LONG, rffi.INT], MuIntValue)),
    ('handle_from_uint64', rffi.CCallback([MuCtxPtr, rffi.ULONG, rffi.INT], MuIntValue)),
    ('handle_from_uint64s', rffi.CCallback([MuCtxPtr, rffi.ULONGP, MuArraySize, rffi.INT], MuIntValue)),
    ('handle_from_float', rffi.CCallback([MuCtxPtr, rffi.FLOAT], MuFloatValue)),
    ('handle_from_double', rffi.CCallback([MuCtxPtr, rffi.DOUBLE], MuDoubleValue)),
    ('handle_from_ptr', rffi.CCallback([MuCtxPtr, MuID, MuCPtr], MuUPtrValue)),
    ('handle_from_fp', rffi.CCallback([MuCtxPtr, MuID, MuCFP], MuUFPValue)),
    ('handle_to_sint8', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.CHAR)),
    ('handle_to_uint8', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.UCHAR)),
    ('handle_to_sint16', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.SHORT)),
    ('handle_to_uint16', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.USHORT)),
    ('handle_to_sint32', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.INT)),
    ('handle_to_uint32', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.UINT)),
    ('handle_to_sint64', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.LONG)),
    ('handle_to_uint64', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.ULONG)),
    ('handle_to_float', rffi.CCallback([MuCtxPtr, MuFloatValue], rffi.FLOAT)),
    ('handle_to_double', rffi.CCallback([MuCtxPtr, MuDoubleValue], rffi.DOUBLE)),
    ('handle_to_ptr', rffi.CCallback([MuCtxPtr, MuUPtrValue], MuCPtr)),
    ('handle_to_fp', rffi.CCallback([MuCtxPtr, MuUFPValue], MuCFP)),
    ('handle_from_const', rffi.CCallback([MuCtxPtr, MuID], MuValue)),
    ('handle_from_global', rffi.CCallback([MuCtxPtr, MuID], MuIRefValue)),
    ('handle_from_func', rffi.CCallback([MuCtxPtr, MuID], MuFuncRefValue)),
    ('handle_from_expose', rffi.CCallback([MuCtxPtr, MuID], MuValue)),
    ('delete_value', rffi.CCallback([MuCtxPtr, MuValue], lltype.Void)),
    ('ref_eq', rffi.CCallback([MuCtxPtr, MuGenRefValue, MuGenRefValue], MuBool)),
    ('ref_ult', rffi.CCallback([MuCtxPtr, MuIRefValue, MuIRefValue], MuBool)),
    ('extract_value', rffi.CCallback([MuCtxPtr, MuStructValue, rffi.INT], MuValue)),
    ('insert_value', rffi.CCallback([MuCtxPtr, MuStructValue, rffi.INT, MuValue], MuStructValue)),
    ('extract_element', rffi.CCallback([MuCtxPtr, MuSeqValue, MuIntValue], MuValue)),
    ('insert_element', rffi.CCallback([MuCtxPtr, MuSeqValue, MuIntValue, MuValue], MuSeqValue)),
    ('new_fixed', rffi.CCallback([MuCtxPtr, MuID], MuRefValue)),
    ('new_hybrid', rffi.CCallback([MuCtxPtr, MuID, MuIntValue], MuRefValue)),
    ('refcast', rffi.CCallback([MuCtxPtr, MuGenRefValue, MuID], MuGenRefValue)),
    ('get_iref', rffi.CCallback([MuCtxPtr, MuRefValue], MuIRefValue)),
    ('get_field_iref', rffi.CCallback([MuCtxPtr, MuIRefValue, rffi.INT], MuIRefValue)),
    ('get_elem_iref', rffi.CCallback([MuCtxPtr, MuIRefValue, MuIntValue], MuIRefValue)),
    ('shift_iref', rffi.CCallback([MuCtxPtr, MuIRefValue, MuIntValue], MuIRefValue)),
    ('get_var_part_iref', rffi.CCallback([MuCtxPtr, MuIRefValue], MuIRefValue)),
    ('load', rffi.CCallback([MuCtxPtr, MuMemOrd._lltype, MuIRefValue], MuValue)),
    ('store', rffi.CCallback([MuCtxPtr, MuMemOrd._lltype, MuIRefValue, MuValue], lltype.Void)),
    ('cmpxchg',
     rffi.CCallback([MuCtxPtr, MuMemOrd._lltype, MuMemOrd._lltype, MuBool, MuIRefValue, MuValue, MuValue, MuBoolPtr],
                    MuValue)),
    (
    'atomicrmw', rffi.CCallback([MuCtxPtr, MuMemOrd._lltype, MuAtomicRMWOptr._lltype, MuIRefValue, MuValue], MuValue)),
    ('fence', rffi.CCallback([MuCtxPtr, MuMemOrd._lltype], lltype.Void)),
    ('new_stack', rffi.CCallback([MuCtxPtr, MuFuncRefValue], MuStackRefValue)),
    ('new_thread_nor',
     rffi.CCallback([MuCtxPtr, MuStackRefValue, MuRefValue, MuValuePtr, MuArraySize], MuThreadRefValue)),
    ('new_thread_exc', rffi.CCallback([MuCtxPtr, MuStackRefValue, MuRefValue, MuRefValue], MuThreadRefValue)),
    ('kill_stack', rffi.CCallback([MuCtxPtr, MuStackRefValue], lltype.Void)),
    ('set_threadlocal', rffi.CCallback([MuCtxPtr, MuThreadRefValue, MuRefValue], lltype.Void)),
    ('get_threadlocal', rffi.CCallback([MuCtxPtr, MuThreadRefValue], MuRefValue)),
    ('new_cursor', rffi.CCallback([MuCtxPtr, MuStackRefValue], MuFCRefValue)),
    ('next_frame', rffi.CCallback([MuCtxPtr, MuFCRefValue], lltype.Void)),
    ('copy_cursor', rffi.CCallback([MuCtxPtr, MuFCRefValue], MuFCRefValue)),
    ('close_cursor', rffi.CCallback([MuCtxPtr, MuFCRefValue], lltype.Void)),
    ('cur_func', rffi.CCallback([MuCtxPtr, MuFCRefValue], MuID)),
    ('cur_func_ver', rffi.CCallback([MuCtxPtr, MuFCRefValue], MuID)),
    ('cur_inst', rffi.CCallback([MuCtxPtr, MuFCRefValue], MuID)),
    ('dump_keepalives', rffi.CCallback([MuCtxPtr, MuFCRefValue, MuValuePtr], lltype.Void)),
    ('pop_frames_to', rffi.CCallback([MuCtxPtr, MuFCRefValue], lltype.Void)),
    ('push_frame', rffi.CCallback([MuCtxPtr, MuStackRefValue, MuFuncRefValue], lltype.Void)),
    ('tr64_is_fp', rffi.CCallback([MuCtxPtr, MuTagRef64Value], MuBool)),
    ('tr64_is_int', rffi.CCallback([MuCtxPtr, MuTagRef64Value], MuBool)),
    ('tr64_is_ref', rffi.CCallback([MuCtxPtr, MuTagRef64Value], MuBool)),
    ('tr64_to_fp', rffi.CCallback([MuCtxPtr, MuTagRef64Value], MuDoubleValue)),
    ('tr64_to_int', rffi.CCallback([MuCtxPtr, MuTagRef64Value], MuIntValue)),
    ('tr64_to_ref', rffi.CCallback([MuCtxPtr, MuTagRef64Value], MuRefValue)),
    ('tr64_to_tag', rffi.CCallback([MuCtxPtr, MuTagRef64Value], MuIntValue)),
    ('tr64_from_fp', rffi.CCallback([MuCtxPtr, MuDoubleValue], MuTagRef64Value)),
    ('tr64_from_int', rffi.CCallback([MuCtxPtr, MuIntValue], MuTagRef64Value)),
    ('tr64_from_ref', rffi.CCallback([MuCtxPtr, MuRefValue, MuIntValue], MuTagRef64Value)),
    ('enable_watchpoint', rffi.CCallback([MuCtxPtr, MuWPID], lltype.Void)),
    ('disable_watchpoint', rffi.CCallback([MuCtxPtr, MuWPID], lltype.Void)),
    ('pin', rffi.CCallback([MuCtxPtr, MuValue], MuUPtrValue)),
    ('unpin', rffi.CCallback([MuCtxPtr, MuValue], lltype.Void)),
    ('expose', rffi.CCallback([MuCtxPtr, MuFuncRefValue, MuCallConv._lltype, MuIntValue], MuValue)),
    ('unexpose', rffi.CCallback([MuCtxPtr, MuCallConv._lltype, MuValue], lltype.Void)),
    ('new_bundle', rffi.CCallback([MuCtxPtr], MuBundleNode)),
    ('load_bundle_from_node', rffi.CCallback([MuCtxPtr, MuBundleNode], lltype.Void)),
    ('abort_bundle_node', rffi.CCallback([MuCtxPtr, MuBundleNode], lltype.Void)),
    ('get_node', rffi.CCallback([MuCtxPtr, MuBundleNode, MuID], MuChildNode)),
    ('get_id', rffi.CCallback([MuCtxPtr, MuBundleNode, MuChildNode], MuID)),
    ('set_name', rffi.CCallback([MuCtxPtr, MuBundleNode, MuChildNode, MuName], lltype.Void)),
    ('new_type_int', rffi.CCallback([MuCtxPtr, MuBundleNode, rffi.INT], MuTypeNode)),
    ('new_type_float', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_type_double', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_type_uptr', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('set_type_uptr', rffi.CCallback([MuCtxPtr, MuTypeNode, MuTypeNode], lltype.Void)),
    ('new_type_ufuncptr', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('set_type_ufuncptr', rffi.CCallback([MuCtxPtr, MuTypeNode, MuFuncSigNode], lltype.Void)),
    ('new_type_struct', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNodePtr, MuArraySize], MuTypeNode)),
    ('new_type_hybrid', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNodePtr, MuArraySize, MuTypeNode], MuTypeNode)),
    ('new_type_array', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode, rffi.ULONG], MuTypeNode)),
    ('new_type_vector', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode, rffi.ULONG], MuTypeNode)),
    ('new_type_void', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_type_ref', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('set_type_ref', rffi.CCallback([MuCtxPtr, MuTypeNode, MuTypeNode], lltype.Void)),
    ('new_type_iref', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('set_type_iref', rffi.CCallback([MuCtxPtr, MuTypeNode, MuTypeNode], lltype.Void)),
    ('new_type_weakref', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('set_type_weakref', rffi.CCallback([MuCtxPtr, MuTypeNode, MuTypeNode], lltype.Void)),
    ('new_type_funcref', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('set_type_funcref', rffi.CCallback([MuCtxPtr, MuTypeNode, MuFuncSigNode], lltype.Void)),
    ('new_type_tagref64', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_type_threadref', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_type_stackref', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_type_framecursorref', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_type_irnoderef', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_funcsig',
     rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNodePtr, MuArraySize, MuTypeNodePtr, MuArraySize], MuFuncSigNode)),
    ('new_const_int', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode, rffi.ULONG], MuConstNode)),
    ('new_const_int_ex', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode, rffi.ULONGP, MuArraySize], MuConstNode)),
    ('new_const_float', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode, rffi.FLOAT], MuConstNode)),
    ('new_const_double', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode, rffi.DOUBLE], MuConstNode)),
    ('new_const_null', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode], MuConstNode)),
    ('new_const_seq', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode, MuConstNodePtr, MuArraySize], MuConstNode)),
    ('new_global_cell', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode], MuGlobalNode)),
    ('new_func', rffi.CCallback([MuCtxPtr, MuBundleNode, MuFuncSigNode], MuFuncNode)),
    ('new_func_ver', rffi.CCallback([MuCtxPtr, MuBundleNode, MuFuncNode], MuFuncVerNode)),
    ('new_exp_func',
     rffi.CCallback([MuCtxPtr, MuBundleNode, MuFuncNode, MuCallConv._lltype, MuConstNode], MuExpFuncNode)),
    ('new_bb', rffi.CCallback([MuCtxPtr, MuFuncVerNode], MuBBNode)),
    ('new_nor_param', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode], MuNorParamNode)),
    ('new_exc_param', rffi.CCallback([MuCtxPtr, MuBBNode], MuExcParamNode)),
    ('new_inst_res', rffi.CCallback([MuCtxPtr, MuInstNode], MuInstResNode)),
    ('add_dest',
     rffi.CCallback([MuCtxPtr, MuInstNode, MuDestKind._lltype, MuBBNode, MuVarNodePtr, MuArraySize], lltype.Void)),
    ('add_keepalives', rffi.CCallback([MuCtxPtr, MuInstNode, MuLocalVarNodePtr, MuArraySize], lltype.Void)),
    ('new_binop',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuBinOptr._lltype, MuTypeNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_cmp', rffi.CCallback([MuCtxPtr, MuBBNode, MuCmpOptr._lltype, MuTypeNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_conv',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuConvOptr._lltype, MuTypeNode, MuTypeNode, MuVarNode], MuInstNode)),
    ('new_select',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_branch', rffi.CCallback([MuCtxPtr, MuBBNode], MuInstNode)),
    ('new_branch2', rffi.CCallback([MuCtxPtr, MuBBNode, MuVarNode], MuInstNode)),
    ('new_switch', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuVarNode], MuInstNode)),
    ('add_switch_dest',
     rffi.CCallback([MuCtxPtr, MuInstNode, MuConstNode, MuBBNode, MuVarNodePtr, MuArraySize], lltype.Void)),
    (
    'new_call', rffi.CCallback([MuCtxPtr, MuBBNode, MuFuncSigNode, MuVarNode, MuVarNodePtr, MuArraySize], MuInstNode)),
    ('new_tailcall',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuFuncSigNode, MuVarNode, MuVarNodePtr, MuArraySize], MuInstNode)),
    ('new_ret', rffi.CCallback([MuCtxPtr, MuBBNode, MuVarNodePtr, MuArraySize], MuInstNode)),
    ('new_throw', rffi.CCallback([MuCtxPtr, MuBBNode, MuVarNode], MuInstNode)),
    ('new_extractvalue', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, rffi.INT, MuVarNode], MuInstNode)),
    ('new_insertvalue', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, rffi.INT, MuVarNode, MuVarNode], MuInstNode)),
    ('new_extractelement',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_insertelement',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_shufflevector',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_new', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode], MuInstNode)),
    ('new_newhybrid', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode], MuInstNode)),
    ('new_alloca', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode], MuInstNode)),
    ('new_allocahybrid', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode], MuInstNode)),
    ('new_getiref', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuVarNode], MuInstNode)),
    ('new_getfieldiref', rffi.CCallback([MuCtxPtr, MuBBNode, MuBool, MuTypeNode, rffi.INT, MuVarNode], MuInstNode)),
    ('new_getelemiref',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuBool, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_shiftiref',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuBool, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_getvarpartiref', rffi.CCallback([MuCtxPtr, MuBBNode, MuBool, MuTypeNode, MuVarNode], MuInstNode)),
    ('new_load', rffi.CCallback([MuCtxPtr, MuBBNode, MuBool, MuMemOrd._lltype, MuTypeNode, MuVarNode], MuInstNode)),
    ('new_store',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuBool, MuMemOrd._lltype, MuTypeNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_cmpxchg', rffi.CCallback(
        [MuCtxPtr, MuBBNode, MuBool, MuBool, MuMemOrd._lltype, MuMemOrd._lltype, MuTypeNode, MuVarNode, MuVarNode,
         MuVarNode], MuInstNode)),
    ('new_atomicrmw', rffi.CCallback(
        [MuCtxPtr, MuBBNode, MuBool, MuMemOrd._lltype, MuAtomicRMWOptr._lltype, MuTypeNode, MuVarNode, MuVarNode],
        MuInstNode)),
    ('new_fence', rffi.CCallback([MuCtxPtr, MuBBNode, MuMemOrd._lltype], MuInstNode)),
    ('new_trap', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNodePtr, MuArraySize], MuInstNode)),
    ('new_watchpoint', rffi.CCallback([MuCtxPtr, MuBBNode, MuWPID, MuTypeNodePtr, MuArraySize], MuInstNode)),
    ('new_wpbranch', rffi.CCallback([MuCtxPtr, MuBBNode, MuWPID], MuInstNode)),
    ('new_ccall', rffi.CCallback(
        [MuCtxPtr, MuBBNode, MuCallConv._lltype, MuTypeNode, MuFuncSigNode, MuVarNode, MuVarNodePtr, MuArraySize],
        MuInstNode)),
    ('new_newthread', rffi.CCallback([MuCtxPtr, MuBBNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_swapstack_ret', rffi.CCallback([MuCtxPtr, MuBBNode, MuVarNode, MuTypeNodePtr, MuArraySize], MuInstNode)),
    ('new_swapstack_kill', rffi.CCallback([MuCtxPtr, MuBBNode, MuVarNode], MuInstNode)),
    ('set_newstack_pass_values',
     rffi.CCallback([MuCtxPtr, MuInstNode, MuTypeNodePtr, MuVarNodePtr, MuArraySize], lltype.Void)),
    ('set_newstack_throw_exc', rffi.CCallback([MuCtxPtr, MuInstNode, MuVarNode], lltype.Void)),
    ('new_comminst', rffi.CCallback(
        [MuCtxPtr, MuBBNode, MuCommInst._lltype, MuFlagPtr, MuArraySize, MuTypeNodePtr, MuArraySize, MuFuncSigNodePtr,
         MuArraySize, MuVarNodePtr, MuArraySize], MuInstNode)),
))

mu_new = rffi.llexternal('mu_refimpl2_new', [], MuVMPtr, compilation_info=eci)
mu_close = rffi.llexternal('mu_refimpl2_close', [MuVMPtr], lltype.Void, compilation_info=eci)