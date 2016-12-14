"""
Mu API RPython binding.
This file is auto-generated and then added a few minor modifications.
Note: environment variable $MU needs to be defined to point to the reference implementation!
"""

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype
from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rlib.objectmodel import specialize
import os

libmu_dir = os.path.join(os.getenv('MU_ZEBU'), 'target', 'debug')
eci = ExternalCompilationInfo(libraries=['mu'],
                              library_dirs=[libmu_dir])


# -------------------------------------------------------------------------------------------------------
# Type definitions
MuValue = rffi.VOIDP
MuValuePtr = rffi.CArrayPtr(MuValue)
MuSeqValue = MuValue
MuSeqValuePtr = rffi.CArrayPtr(MuSeqValue)
MuGenRefValue = MuValue
MuGenRefValuePtr = rffi.CArrayPtr(MuGenRefValue)
MuIntValue = MuValue
MuIntValuePtr = rffi.CArrayPtr(MuIntValue)
MuFloatValue = MuValue
MuFloatValuePtr = rffi.CArrayPtr(MuFloatValue)
MuDoubleValue = MuValue
MuDoubleValuePtr = rffi.CArrayPtr(MuDoubleValue)
MuUPtrValue = MuValue
MuUPtrValuePtr = rffi.CArrayPtr(MuUPtrValue)
MuUFPValue = MuValue
MuUFPValuePtr = rffi.CArrayPtr(MuUFPValue)
MuStructValue = MuValue
MuStructValuePtr = rffi.CArrayPtr(MuStructValue)
MuArrayValue = MuSeqValue
MuArrayValuePtr = rffi.CArrayPtr(MuArrayValue)
MuVectorValue = MuSeqValue
MuVectorValuePtr = rffi.CArrayPtr(MuVectorValue)
MuRefValue = MuGenRefValue
MuRefValuePtr = rffi.CArrayPtr(MuRefValue)
MuIRefValue = MuGenRefValue
MuIRefValuePtr = rffi.CArrayPtr(MuIRefValue)
MuTagRef64Value = MuGenRefValue
MuTagRef64ValuePtr = rffi.CArrayPtr(MuTagRef64Value)
MuFuncRefValue = MuGenRefValue
MuFuncRefValuePtr = rffi.CArrayPtr(MuFuncRefValue)
MuThreadRefValue = MuGenRefValue
MuThreadRefValuePtr = rffi.CArrayPtr(MuThreadRefValue)
MuStackRefValue = MuGenRefValue
MuStackRefValuePtr = rffi.CArrayPtr(MuStackRefValue)
MuFCRefValue = MuGenRefValue
MuFCRefValuePtr = rffi.CArrayPtr(MuFCRefValue)
MuIBRefValue = MuGenRefValue
MuIBRefValuePtr = rffi.CArrayPtr(MuIBRefValue)
MuCString = rffi.CCHARP
MuCStringPtr = rffi.CArrayPtr(MuCString)
MuID = rffi.UINT
MuIDPtr = rffi.CArrayPtr(MuID)
MuName = MuCString
MuNamePtr = rffi.CArrayPtr(MuName)
MuCPtr = rffi.VOIDP
MuCPtrPtr = rffi.CArrayPtr(MuCPtr)
MuCFP = rffi.VOIDP
MuCFPPtr = rffi.CArrayPtr(MuCFP)
MuBool = rffi.INT
MuBoolPtr = rffi.CArrayPtr(MuBool)
MuArraySize = rffi.UINTPTR_T
MuArraySizePtr = rffi.CArrayPtr(MuArraySize)
MuWPID = rffi.UINT
MuWPIDPtr = rffi.CArrayPtr(MuWPID)
MuFlag = rffi.UINT
MuFlagPtr = rffi.CArrayPtr(MuFlag)
MuTrapHandlerResult = MuFlag
MuTrapHandlerResultPtr = rffi.CArrayPtr(MuTrapHandlerResult)
MuBinOpStatus = MuFlag
MuBinOpStatusPtr = rffi.CArrayPtr(MuBinOpStatus)
MuTypeNode = MuID
MuTypeNodePtr = rffi.CArrayPtr(MuTypeNode)
MuFuncSigNode = MuID
MuFuncSigNodePtr = rffi.CArrayPtr(MuFuncSigNode)
MuVarNode = MuID
MuVarNodePtr = rffi.CArrayPtr(MuVarNode)
MuGlobalVarNode = MuID
MuGlobalVarNodePtr = rffi.CArrayPtr(MuGlobalVarNode)
MuLocalVarNode = MuID
MuLocalVarNodePtr = rffi.CArrayPtr(MuLocalVarNode)
MuConstNode = MuID
MuConstNodePtr = rffi.CArrayPtr(MuConstNode)
MuFuncNode = MuID
MuFuncNodePtr = rffi.CArrayPtr(MuFuncNode)
MuFuncVerNode = MuID
MuFuncVerNodePtr = rffi.CArrayPtr(MuFuncVerNode)
MuBBNode = MuID
MuBBNodePtr = rffi.CArrayPtr(MuBBNode)
MuInstNode = MuID
MuInstNodePtr = rffi.CArrayPtr(MuInstNode)
MuDestClause = MuID
MuDestClausePtr = rffi.CArrayPtr(MuDestClause)
MuExcClause = MuID
MuExcClausePtr = rffi.CArrayPtr(MuExcClause)
MuKeepaliveClause = MuID
MuKeepaliveClausePtr = rffi.CArrayPtr(MuKeepaliveClause)
MuCurStackClause = MuID
MuCurStackClausePtr = rffi.CArrayPtr(MuCurStackClause)
MuNewStackClause = MuID
MuNewStackClausePtr = rffi.CArrayPtr(MuNewStackClause)
_MuVM = lltype.ForwardReference()
_MuVMPtr = lltype.Ptr(_MuVM)
_MuCtx = lltype.ForwardReference()
_MuCtxPtr = lltype.Ptr(_MuCtx)
_MuIRBuilder = lltype.ForwardReference()
_MuIRBuilderPtr = lltype.Ptr(_MuIRBuilder)
MuValuesFreer = rffi.CCallback([MuValuePtr, MuCPtr], lltype.Void)
MuValuesFreerPtr = rffi.CArrayPtr(MuValuesFreer)
MuTrapHandler = rffi.CCallback([
    _MuCtxPtr, MuThreadRefValue, MuStackRefValue, MuWPID,   # input
    MuTrapHandlerResultPtr, MuStackRefValuePtr, rffi.CArray(MuValuePtr), MuArraySizePtr,
    MuValuesFreerPtr, MuCPtrPtr, MuRefValuePtr,             # output
    MuCPtr  #input
], lltype.Void)
MuTrapHandlerPtr = rffi.CArrayPtr(MuTrapHandler)

# -------------------------------------------------------------------------------------------------------
# Flags
class MuTrapHandlerResult:
    THREAD_EXIT = rffi.cast(MuFlag, 0x00)
    REBIND_PASS_VALUES = rffi.cast(MuFlag, 0x01)
    REBIND_THROW_EXC = rffi.cast(MuFlag, 0x02)
class MuBinOpStatus:
    N = rffi.cast(MuFlag, 0x01)
    Z = rffi.cast(MuFlag, 0x02)
    C = rffi.cast(MuFlag, 0x04)
    V = rffi.cast(MuFlag, 0x08)
class MuBinOptr:
    ADD = rffi.cast(MuFlag, 0x01)
    SUB = rffi.cast(MuFlag, 0x02)
    MUL = rffi.cast(MuFlag, 0x03)
    SDIV = rffi.cast(MuFlag, 0x04)
    SREM = rffi.cast(MuFlag, 0x05)
    UDIV = rffi.cast(MuFlag, 0x06)
    UREM = rffi.cast(MuFlag, 0x07)
    SHL = rffi.cast(MuFlag, 0x08)
    LSHR = rffi.cast(MuFlag, 0x09)
    ASHR = rffi.cast(MuFlag, 0x0A)
    AND = rffi.cast(MuFlag, 0x0B)
    OR = rffi.cast(MuFlag, 0x0C)
    XOR = rffi.cast(MuFlag, 0x0D)
    FADD = rffi.cast(MuFlag, 0xB0)
    FSUB = rffi.cast(MuFlag, 0xB1)
    FMUL = rffi.cast(MuFlag, 0xB2)
    FDIV = rffi.cast(MuFlag, 0xB3)
    FREM = rffi.cast(MuFlag, 0xB4)
class MuCmpOptr:
    EQ = rffi.cast(MuFlag, 0x20)
    NE = rffi.cast(MuFlag, 0x21)
    SGE = rffi.cast(MuFlag, 0x22)
    SGT = rffi.cast(MuFlag, 0x23)
    SLE = rffi.cast(MuFlag, 0x24)
    SLT = rffi.cast(MuFlag, 0x25)
    UGE = rffi.cast(MuFlag, 0x26)
    UGT = rffi.cast(MuFlag, 0x27)
    ULE = rffi.cast(MuFlag, 0x28)
    ULT = rffi.cast(MuFlag, 0x29)
    FFALSE = rffi.cast(MuFlag, 0xC0)
    FTRUE = rffi.cast(MuFlag, 0xC1)
    FUNO = rffi.cast(MuFlag, 0xC2)
    FUEQ = rffi.cast(MuFlag, 0xC3)
    FUNE = rffi.cast(MuFlag, 0xC4)
    FUGT = rffi.cast(MuFlag, 0xC5)
    FUGE = rffi.cast(MuFlag, 0xC6)
    FULT = rffi.cast(MuFlag, 0xC7)
    FULE = rffi.cast(MuFlag, 0xC8)
    FORD = rffi.cast(MuFlag, 0xC9)
    FOEQ = rffi.cast(MuFlag, 0xCA)
    FONE = rffi.cast(MuFlag, 0xCB)
    FOGT = rffi.cast(MuFlag, 0xCC)
    FOGE = rffi.cast(MuFlag, 0xCD)
    FOLT = rffi.cast(MuFlag, 0xCE)
    FOLE = rffi.cast(MuFlag, 0xCF)
class MuConvOptr:
    TRUNC = rffi.cast(MuFlag, 0x30)
    ZEXT = rffi.cast(MuFlag, 0x31)
    SEXT = rffi.cast(MuFlag, 0x32)
    FPTRUNC = rffi.cast(MuFlag, 0x33)
    FPEXT = rffi.cast(MuFlag, 0x34)
    FPTOUI = rffi.cast(MuFlag, 0x35)
    FPTOSI = rffi.cast(MuFlag, 0x36)
    UITOFP = rffi.cast(MuFlag, 0x37)
    SITOFP = rffi.cast(MuFlag, 0x38)
    BITCAST = rffi.cast(MuFlag, 0x39)
    REFCAST = rffi.cast(MuFlag, 0x3A)
    PTRCAST = rffi.cast(MuFlag, 0x3B)
class MuMemOrd:
    NOT_ATOMIC = rffi.cast(MuFlag, 0x00)
    RELAXED = rffi.cast(MuFlag, 0x01)
    CONSUME = rffi.cast(MuFlag, 0x02)
    ACQUIRE = rffi.cast(MuFlag, 0x03)
    RELEASE = rffi.cast(MuFlag, 0x04)
    ACQ_REL = rffi.cast(MuFlag, 0x05)
    SEQ_CST = rffi.cast(MuFlag, 0x06)
class MuAtomicRMWOptr:
    XCHG = rffi.cast(MuFlag, 0x00)
    ADD = rffi.cast(MuFlag, 0x01)
    SUB = rffi.cast(MuFlag, 0x02)
    AND = rffi.cast(MuFlag, 0x03)
    NAND = rffi.cast(MuFlag, 0x04)
    OR = rffi.cast(MuFlag, 0x05)
    XOR = rffi.cast(MuFlag, 0x06)
    MAX = rffi.cast(MuFlag, 0x07)
    MIN = rffi.cast(MuFlag, 0x08)
    UMAX = rffi.cast(MuFlag, 0x09)
    UMIN = rffi.cast(MuFlag, 0x0A)
class MuCallConv:
    DEFAULT = rffi.cast(MuFlag, 0x00)
class MuCommInst:
    NEW_STACK = rffi.cast(MuFlag, 0x201)
    KILL_STACK = rffi.cast(MuFlag, 0x202)
    THREAD_EXIT = rffi.cast(MuFlag, 0x203)
    CURRENT_STACK = rffi.cast(MuFlag, 0x204)
    SET_THREADLOCAL = rffi.cast(MuFlag, 0x205)
    GET_THREADLOCAL = rffi.cast(MuFlag, 0x206)
    TR64_IS_FP = rffi.cast(MuFlag, 0x211)
    TR64_IS_INT = rffi.cast(MuFlag, 0x212)
    TR64_IS_REF = rffi.cast(MuFlag, 0x213)
    TR64_FROM_FP = rffi.cast(MuFlag, 0x214)
    TR64_FROM_INT = rffi.cast(MuFlag, 0x215)
    TR64_FROM_REF = rffi.cast(MuFlag, 0x216)
    TR64_TO_FP = rffi.cast(MuFlag, 0x217)
    TR64_TO_INT = rffi.cast(MuFlag, 0x218)
    TR64_TO_REF = rffi.cast(MuFlag, 0x219)
    TR64_TO_TAG = rffi.cast(MuFlag, 0x21a)
    FUTEX_WAIT = rffi.cast(MuFlag, 0x220)
    FUTEX_WAIT_TIMEOUT = rffi.cast(MuFlag, 0x221)
    FUTEX_WAKE = rffi.cast(MuFlag, 0x222)
    FUTEX_CMP_REQUEUE = rffi.cast(MuFlag, 0x223)
    KILL_DEPENDENCY = rffi.cast(MuFlag, 0x230)
    NATIVE_PIN = rffi.cast(MuFlag, 0x240)
    NATIVE_UNPIN = rffi.cast(MuFlag, 0x241)
    NATIVE_GET_ADDR = rffi.cast(MuFlag, 0x242)
    NATIVE_EXPOSE = rffi.cast(MuFlag, 0x243)
    NATIVE_UNEXPOSE = rffi.cast(MuFlag, 0x244)
    NATIVE_GET_COOKIE = rffi.cast(MuFlag, 0x245)
    META_ID_OF = rffi.cast(MuFlag, 0x250)
    META_NAME_OF = rffi.cast(MuFlag, 0x251)
    META_LOAD_BUNDLE = rffi.cast(MuFlag, 0x252)
    META_LOAD_HAIL = rffi.cast(MuFlag, 0x253)
    META_NEW_CURSOR = rffi.cast(MuFlag, 0x254)
    META_NEXT_FRAME = rffi.cast(MuFlag, 0x255)
    META_COPY_CURSOR = rffi.cast(MuFlag, 0x256)
    META_CLOSE_CURSOR = rffi.cast(MuFlag, 0x257)
    META_CUR_FUNC = rffi.cast(MuFlag, 0x258)
    META_CUR_FUNC_VER = rffi.cast(MuFlag, 0x259)
    META_CUR_INST = rffi.cast(MuFlag, 0x25a)
    META_DUMP_KEEPALIVES = rffi.cast(MuFlag, 0x25b)
    META_POP_FRAMES_TO = rffi.cast(MuFlag, 0x25c)
    META_PUSH_FRAME = rffi.cast(MuFlag, 0x25d)
    META_ENABLE_WATCHPOINT = rffi.cast(MuFlag, 0x25e)
    META_DISABLE_WATCHPOINT = rffi.cast(MuFlag, 0x25f)
    META_SET_TRAP_HANDLER = rffi.cast(MuFlag, 0x260)
    IRBUILDER_NEW_IR_BUILDER = rffi.cast(MuFlag, 0x270)
    IRBUILDER_LOAD = rffi.cast(MuFlag, 0x300)
    IRBUILDER_ABORT = rffi.cast(MuFlag, 0x301)
    IRBUILDER_GEN_SYM = rffi.cast(MuFlag, 0x302)
    IRBUILDER_NEW_TYPE_INT = rffi.cast(MuFlag, 0x303)
    IRBUILDER_NEW_TYPE_FLOAT = rffi.cast(MuFlag, 0x304)
    IRBUILDER_NEW_TYPE_DOUBLE = rffi.cast(MuFlag, 0x305)
    IRBUILDER_NEW_TYPE_UPTR = rffi.cast(MuFlag, 0x306)
    IRBUILDER_NEW_TYPE_UFUNCPTR = rffi.cast(MuFlag, 0x307)
    IRBUILDER_NEW_TYPE_STRUCT = rffi.cast(MuFlag, 0x308)
    IRBUILDER_NEW_TYPE_HYBRID = rffi.cast(MuFlag, 0x309)
    IRBUILDER_NEW_TYPE_ARRAY = rffi.cast(MuFlag, 0x30a)
    IRBUILDER_NEW_TYPE_VECTOR = rffi.cast(MuFlag, 0x30b)
    IRBUILDER_NEW_TYPE_VOID = rffi.cast(MuFlag, 0x30c)
    IRBUILDER_NEW_TYPE_REF = rffi.cast(MuFlag, 0x30d)
    IRBUILDER_NEW_TYPE_IREF = rffi.cast(MuFlag, 0x30e)
    IRBUILDER_NEW_TYPE_WEAKREF = rffi.cast(MuFlag, 0x30f)
    IRBUILDER_NEW_TYPE_FUNCREF = rffi.cast(MuFlag, 0x310)
    IRBUILDER_NEW_TYPE_TAGREF64 = rffi.cast(MuFlag, 0x311)
    IRBUILDER_NEW_TYPE_THREADREF = rffi.cast(MuFlag, 0x312)
    IRBUILDER_NEW_TYPE_STACKREF = rffi.cast(MuFlag, 0x313)
    IRBUILDER_NEW_TYPE_FRAMECURSORREF = rffi.cast(MuFlag, 0x314)
    IRBUILDER_NEW_TYPE_IRBUILDERREF = rffi.cast(MuFlag, 0x315)
    IRBUILDER_NEW_FUNCSIG = rffi.cast(MuFlag, 0x316)
    IRBUILDER_NEW_CONST_INT = rffi.cast(MuFlag, 0x317)
    IRBUILDER_NEW_CONST_INT_EX = rffi.cast(MuFlag, 0x318)
    IRBUILDER_NEW_CONST_FLOAT = rffi.cast(MuFlag, 0x319)
    IRBUILDER_NEW_CONST_DOUBLE = rffi.cast(MuFlag, 0x31a)
    IRBUILDER_NEW_CONST_NULL = rffi.cast(MuFlag, 0x31b)
    IRBUILDER_NEW_CONST_SEQ = rffi.cast(MuFlag, 0x31c)
    IRBUILDER_NEW_CONST_EXTERN = rffi.cast(MuFlag, 0x31d)
    IRBUILDER_NEW_GLOBAL_CELL = rffi.cast(MuFlag, 0x31e)
    IRBUILDER_NEW_FUNC = rffi.cast(MuFlag, 0x31f)
    IRBUILDER_NEW_EXP_FUNC = rffi.cast(MuFlag, 0x320)
    IRBUILDER_NEW_FUNC_VER = rffi.cast(MuFlag, 0x321)
    IRBUILDER_NEW_BB = rffi.cast(MuFlag, 0x322)
    IRBUILDER_NEW_DEST_CLAUSE = rffi.cast(MuFlag, 0x323)
    IRBUILDER_NEW_EXC_CLAUSE = rffi.cast(MuFlag, 0x324)
    IRBUILDER_NEW_KEEPALIVE_CLAUSE = rffi.cast(MuFlag, 0x325)
    IRBUILDER_NEW_CSC_RET_WITH = rffi.cast(MuFlag, 0x326)
    IRBUILDER_NEW_CSC_KILL_OLD = rffi.cast(MuFlag, 0x327)
    IRBUILDER_NEW_NSC_PASS_VALUES = rffi.cast(MuFlag, 0x328)
    IRBUILDER_NEW_NSC_THROW_EXC = rffi.cast(MuFlag, 0x329)
    IRBUILDER_NEW_BINOP = rffi.cast(MuFlag, 0x32a)
    IRBUILDER_NEW_BINOP_WITH_STATUS = rffi.cast(MuFlag, 0x32b)
    IRBUILDER_NEW_CMP = rffi.cast(MuFlag, 0x32c)
    IRBUILDER_NEW_CONV = rffi.cast(MuFlag, 0x32d)
    IRBUILDER_NEW_SELECT = rffi.cast(MuFlag, 0x32e)
    IRBUILDER_NEW_BRANCH = rffi.cast(MuFlag, 0x32f)
    IRBUILDER_NEW_BRANCH2 = rffi.cast(MuFlag, 0x330)
    IRBUILDER_NEW_SWITCH = rffi.cast(MuFlag, 0x331)
    IRBUILDER_NEW_CALL = rffi.cast(MuFlag, 0x332)
    IRBUILDER_NEW_TAILCALL = rffi.cast(MuFlag, 0x333)
    IRBUILDER_NEW_RET = rffi.cast(MuFlag, 0x334)
    IRBUILDER_NEW_THROW = rffi.cast(MuFlag, 0x335)
    IRBUILDER_NEW_EXTRACTVALUE = rffi.cast(MuFlag, 0x336)
    IRBUILDER_NEW_INSERTVALUE = rffi.cast(MuFlag, 0x337)
    IRBUILDER_NEW_EXTRACTELEMENT = rffi.cast(MuFlag, 0x338)
    IRBUILDER_NEW_INSERTELEMENT = rffi.cast(MuFlag, 0x339)
    IRBUILDER_NEW_SHUFFLEVECTOR = rffi.cast(MuFlag, 0x33a)
    IRBUILDER_NEW_NEW = rffi.cast(MuFlag, 0x33b)
    IRBUILDER_NEW_NEWHYBRID = rffi.cast(MuFlag, 0x33c)
    IRBUILDER_NEW_ALLOCA = rffi.cast(MuFlag, 0x33d)
    IRBUILDER_NEW_ALLOCAHYBRID = rffi.cast(MuFlag, 0x33e)
    IRBUILDER_NEW_GETIREF = rffi.cast(MuFlag, 0x33f)
    IRBUILDER_NEW_GETFIELDIREF = rffi.cast(MuFlag, 0x340)
    IRBUILDER_NEW_GETELEMIREF = rffi.cast(MuFlag, 0x341)
    IRBUILDER_NEW_SHIFTIREF = rffi.cast(MuFlag, 0x342)
    IRBUILDER_NEW_GETVARPARTIREF = rffi.cast(MuFlag, 0x343)
    IRBUILDER_NEW_LOAD = rffi.cast(MuFlag, 0x344)
    IRBUILDER_NEW_STORE = rffi.cast(MuFlag, 0x345)
    IRBUILDER_NEW_CMPXCHG = rffi.cast(MuFlag, 0x346)
    IRBUILDER_NEW_ATOMICRMW = rffi.cast(MuFlag, 0x347)
    IRBUILDER_NEW_FENCE = rffi.cast(MuFlag, 0x348)
    IRBUILDER_NEW_TRAP = rffi.cast(MuFlag, 0x349)
    IRBUILDER_NEW_WATCHPOINT = rffi.cast(MuFlag, 0x34a)
    IRBUILDER_NEW_WPBRANCH = rffi.cast(MuFlag, 0x34b)
    IRBUILDER_NEW_CCALL = rffi.cast(MuFlag, 0x34c)
    IRBUILDER_NEW_NEWTHREAD = rffi.cast(MuFlag, 0x34d)
    IRBUILDER_NEW_SWAPSTACK = rffi.cast(MuFlag, 0x34e)
    IRBUILDER_NEW_COMMINST = rffi.cast(MuFlag, 0x34f)

MU_NO_ID = rffi.cast(MuID, 0)

# -------------------------------------------------------------------------------------------------------
# OO wrappers
class MuVM:
    def __init__(self, config_str=""):
        with rffi.scoped_str2charp('init_mu ' + config_str) as buf:
            self._mu = mu_fastimpl_new_with_opts(buf)

    def new_context(self):
        # type: () -> MuCtx
        res = MuCtx(self, self._mu.c_new_context(self._mu))
        return res

    def id_of(self, name):
        # type: (str) -> MuID
        with rffi.scoped_str2charp(name) as name_buf:
            res = self._mu.c_id_of(self._mu, name_buf)
            return res

    def name_of(self, id):
        # type: (MuID) -> str
        res = rffi.charp2str(self._mu.c_name_of(self._mu, id))
        return res

    def set_trap_handler(self, trap_handler, userdata):
        # type: (MuTrapHandler, MuCPtr) -> None
        self._mu.c_set_trap_handler(self._mu, trap_handler, userdata)

    def compile_to_sharedlib(self, lib_name, extra_srcs):
        # type: (str, [MuCString]) -> None
        with rffi.scoped_str2charp(lib_name) as lib_name_buf:
            extra_srcs_arr, extra_srcs_sz = lst2arr(MuCString, extra_srcs)
            self._mu.c_compile_to_sharedlib(self._mu, lib_name_buf, extra_srcs_arr, extra_srcs_sz)
            if extra_srcs_arr:
                rffi.free_charpp(extra_srcs_arr)

    def current_thread_as_mu_thread(self, threadlocal):
        # type: (MuCPtr) -> None
        self._mu.c_current_thread_as_mu_thread(self._mu, threadlocal)


class MuCtx:
    def __init__(self, mu, rffi_ctx_ptr):
        self._mu = mu
        self._ctx = rffi_ctx_ptr

    def id_of(self, name):
        # type: (str) -> MuID
        with rffi.scoped_str2charp(name) as name_buf:
            res = self._ctx.c_id_of(self._ctx, name_buf)
            return res

    def name_of(self, id):
        # type: (MuID) -> str
        res = rffi.charp2str(self._ctx.c_name_of(self._ctx, id))
        return res

    def close_context(self):
        # type: () -> None
        self._ctx.c_close_context(self._ctx)

    def load_bundle(self, buf):
        # type: (str) -> None
        with rffi.scoped_str2charp(buf) as buf_buf:
            sz = rffi.cast(MuArraySize, len(buf))
            self._ctx.c_load_bundle(self._ctx, buf_buf, sz)

    def load_hail(self, buf):
        # type: (str) -> None
        with rffi.scoped_str2charp(buf) as buf_buf:
            sz = rffi.cast(MuArraySize, len(buf))
            self._ctx.c_load_hail(self._ctx, buf_buf, sz)

    def handle_from_sint8(self, num, len):
        # type: (int, int) -> MuIntValue
        num_c = rffi.cast(rffi.CHAR, num)
        len_c = rffi.cast(rffi.INT, len)
        res = self._ctx.c_handle_from_sint8(self._ctx, num_c, len_c)
        return res

    def handle_from_uint8(self, num, len):
        # type: (int, int) -> MuIntValue
        num_c = rffi.cast(rffi.UCHAR, num)
        len_c = rffi.cast(rffi.INT, len)
        res = self._ctx.c_handle_from_uint8(self._ctx, num_c, len_c)
        return res

    def handle_from_sint16(self, num, len):
        # type: (int, int) -> MuIntValue
        num_c = rffi.cast(rffi.SHORT, num)
        len_c = rffi.cast(rffi.INT, len)
        res = self._ctx.c_handle_from_sint16(self._ctx, num_c, len_c)
        return res

    def handle_from_uint16(self, num, len):
        # type: (int, int) -> MuIntValue
        num_c = rffi.cast(rffi.USHORT, num)
        len_c = rffi.cast(rffi.INT, len)
        res = self._ctx.c_handle_from_uint16(self._ctx, num_c, len_c)
        return res

    def handle_from_sint32(self, num, len):
        # type: (int, int) -> MuIntValue
        num_c = rffi.cast(rffi.INT, num)
        len_c = rffi.cast(rffi.INT, len)
        res = self._ctx.c_handle_from_sint32(self._ctx, num_c, len_c)
        return res

    def handle_from_uint32(self, num, len):
        # type: (int, int) -> MuIntValue
        num_c = rffi.cast(rffi.UINT, num)
        len_c = rffi.cast(rffi.INT, len)
        res = self._ctx.c_handle_from_uint32(self._ctx, num_c, len_c)
        return res

    def handle_from_sint64(self, num, len):
        # type: (int, int) -> MuIntValue
        num_c = rffi.cast(rffi.LONG, num)
        len_c = rffi.cast(rffi.INT, len)
        res = self._ctx.c_handle_from_sint64(self._ctx, num_c, len_c)
        return res

    def handle_from_uint64(self, num, len):
        # type: (int, int) -> MuIntValue
        num_c = rffi.cast(rffi.ULONG, num)
        len_c = rffi.cast(rffi.INT, len)
        res = self._ctx.c_handle_from_uint64(self._ctx, num_c, len_c)
        return res

    def handle_from_uint64s(self, nums, len):
        # type: ([rffi.ULONG], int) -> MuIntValue
        nums_arr, nums_sz = lst2arr(rffi.ULONG, nums)
        len_c = rffi.cast(rffi.INT, len)
        res = self._ctx.c_handle_from_uint64s(self._ctx, nums_arr, nums_sz, len_c)
        if nums_arr:
            lltype.free(nums_arr, flavor='raw')
        return res

    def handle_from_float(self, num):
        # type: (float) -> MuFloatValue
        num_c = rffi.cast(rffi.FLOAT, num)
        res = self._ctx.c_handle_from_float(self._ctx, num_c)
        return res

    def handle_from_double(self, num):
        # type: (float) -> MuDoubleValue
        num_c = rffi.cast(rffi.DOUBLE, num)
        res = self._ctx.c_handle_from_double(self._ctx, num_c)
        return res

    def handle_from_ptr(self, mu_type, ptr):
        # type: (MuID, MuCPtr) -> MuUPtrValue
        res = self._ctx.c_handle_from_ptr(self._ctx, mu_type, ptr)
        return res

    def handle_from_fp(self, mu_type, fp):
        # type: (MuID, MuCFP) -> MuUFPValue
        res = self._ctx.c_handle_from_fp(self._ctx, mu_type, fp)
        return res

    def handle_to_sint8(self, opnd):
        # type: (MuIntValue) -> int
        res = int(self._ctx.c_handle_to_sint8(self._ctx, opnd))
        return res

    def handle_to_uint8(self, opnd):
        # type: (MuIntValue) -> int
        res = int(self._ctx.c_handle_to_uint8(self._ctx, opnd))
        return res

    def handle_to_sint16(self, opnd):
        # type: (MuIntValue) -> int
        res = int(self._ctx.c_handle_to_sint16(self._ctx, opnd))
        return res

    def handle_to_uint16(self, opnd):
        # type: (MuIntValue) -> int
        res = int(self._ctx.c_handle_to_uint16(self._ctx, opnd))
        return res

    def handle_to_sint32(self, opnd):
        # type: (MuIntValue) -> int
        res = int(self._ctx.c_handle_to_sint32(self._ctx, opnd))
        return res

    def handle_to_uint32(self, opnd):
        # type: (MuIntValue) -> int
        res = int(self._ctx.c_handle_to_uint32(self._ctx, opnd))
        return res

    def handle_to_sint64(self, opnd):
        # type: (MuIntValue) -> int
        res = int(self._ctx.c_handle_to_sint64(self._ctx, opnd))
        return res

    def handle_to_uint64(self, opnd):
        # type: (MuIntValue) -> int
        res = int(self._ctx.c_handle_to_uint64(self._ctx, opnd))
        return res

    def handle_to_float(self, opnd):
        # type: (MuFloatValue) -> float
        res = float(self._ctx.c_handle_to_float(self._ctx, opnd))
        return res

    def handle_to_double(self, opnd):
        # type: (MuDoubleValue) -> float
        res = float(self._ctx.c_handle_to_double(self._ctx, opnd))
        return res

    def handle_to_ptr(self, opnd):
        # type: (MuUPtrValue) -> MuCPtr
        res = self._ctx.c_handle_to_ptr(self._ctx, opnd)
        return res

    def handle_to_fp(self, opnd):
        # type: (MuUFPValue) -> MuCFP
        res = self._ctx.c_handle_to_fp(self._ctx, opnd)
        return res

    def handle_from_const(self, id):
        # type: (MuID) -> MuValue
        res = self._ctx.c_handle_from_const(self._ctx, id)
        return res

    def handle_from_global(self, id):
        # type: (MuID) -> MuIRefValue
        res = self._ctx.c_handle_from_global(self._ctx, id)
        return res

    def handle_from_func(self, id):
        # type: (MuID) -> MuFuncRefValue
        res = self._ctx.c_handle_from_func(self._ctx, id)
        return res

    def handle_from_expose(self, id):
        # type: (MuID) -> MuValue
        res = self._ctx.c_handle_from_expose(self._ctx, id)
        return res

    def delete_value(self, opnd):
        # type: (MuValue) -> None
        self._ctx.c_delete_value(self._ctx, opnd)

    def ref_eq(self, lhs, rhs):
        # type: (MuGenRefValue, MuGenRefValue) -> bool
        res = bool(self._ctx.c_ref_eq(self._ctx, lhs, rhs))
        return res

    def ref_ult(self, lhs, rhs):
        # type: (MuIRefValue, MuIRefValue) -> bool
        res = bool(self._ctx.c_ref_ult(self._ctx, lhs, rhs))
        return res

    def extract_value(self, str, index):
        # type: (MuStructValue, int) -> MuValue
        index_c = rffi.cast(rffi.INT, index)
        res = self._ctx.c_extract_value(self._ctx, str, index_c)
        return res

    def insert_value(self, str, index, newval):
        # type: (MuStructValue, int, MuValue) -> MuStructValue
        index_c = rffi.cast(rffi.INT, index)
        res = self._ctx.c_insert_value(self._ctx, str, index_c, newval)
        return res

    def extract_element(self, str, index):
        # type: (MuSeqValue, MuIntValue) -> MuValue
        res = self._ctx.c_extract_element(self._ctx, str, index)
        return res

    def insert_element(self, str, index, newval):
        # type: (MuSeqValue, MuIntValue, MuValue) -> MuSeqValue
        res = self._ctx.c_insert_element(self._ctx, str, index, newval)
        return res

    def new_fixed(self, mu_type):
        # type: (MuID) -> MuRefValue
        res = self._ctx.c_new_fixed(self._ctx, mu_type)
        return res

    def new_hybrid(self, mu_type, length):
        # type: (MuID, MuIntValue) -> MuRefValue
        res = self._ctx.c_new_hybrid(self._ctx, mu_type, length)
        return res

    def refcast(self, opnd, new_type):
        # type: (MuGenRefValue, MuID) -> MuGenRefValue
        res = self._ctx.c_refcast(self._ctx, opnd, new_type)
        return res

    def get_iref(self, opnd):
        # type: (MuRefValue) -> MuIRefValue
        res = self._ctx.c_get_iref(self._ctx, opnd)
        return res

    def get_field_iref(self, opnd, field):
        # type: (MuIRefValue, int) -> MuIRefValue
        field_c = rffi.cast(rffi.INT, field)
        res = self._ctx.c_get_field_iref(self._ctx, opnd, field_c)
        return res

    def get_elem_iref(self, opnd, index):
        # type: (MuIRefValue, MuIntValue) -> MuIRefValue
        res = self._ctx.c_get_elem_iref(self._ctx, opnd, index)
        return res

    def shift_iref(self, opnd, offset):
        # type: (MuIRefValue, MuIntValue) -> MuIRefValue
        res = self._ctx.c_shift_iref(self._ctx, opnd, offset)
        return res

    def get_var_part_iref(self, opnd):
        # type: (MuIRefValue) -> MuIRefValue
        res = self._ctx.c_get_var_part_iref(self._ctx, opnd)
        return res

    def load(self, ord, loc):
        # type: (MuFlag, MuIRefValue) -> MuValue
        res = self._ctx.c_load(self._ctx, ord, loc)
        return res

    def store(self, ord, loc, newval):
        # type: (MuFlag, MuIRefValue, MuValue) -> None
        self._ctx.c_store(self._ctx, ord, loc, newval)

    def cmpxchg(self, ord_succ, ord_fail, weak, loc, expected, desired, is_succ):
        # type: (MuFlag, MuFlag, bool, MuIRefValue, MuValue, MuValue, MuBoolPtr) -> MuValue
        weak_c = rffi.cast(MuBool, weak)
        res = self._ctx.c_cmpxchg(self._ctx, ord_succ, ord_fail, weak_c, loc, expected, desired, is_succ)
        return res

    def atomicrmw(self, ord, op, loc, opnd):
        # type: (MuFlag, MuFlag, MuIRefValue, MuValue) -> MuValue
        res = self._ctx.c_atomicrmw(self._ctx, ord, op, loc, opnd)
        return res

    def fence(self, ord):
        # type: (MuFlag) -> None
        self._ctx.c_fence(self._ctx, ord)

    def new_stack(self, func):
        # type: (MuFuncRefValue) -> MuStackRefValue
        res = self._ctx.c_new_stack(self._ctx, func)
        return res

    def new_thread_nor(self, stack, threadlocal, vals):
        # type: (MuStackRefValue, MuRefValue, [MuValue]) -> MuThreadRefValue
        vals_arr, vals_sz = lst2arr(MuValue, vals)
        res = self._ctx.c_new_thread_nor(self._ctx, stack, threadlocal, vals_arr, vals_sz)
        if vals_arr:
            lltype.free(vals_arr, flavor='raw')
        return res

    def new_thread_exc(self, stack, threadlocal, exc):
        # type: (MuStackRefValue, MuRefValue, MuRefValue) -> MuThreadRefValue
        res = self._ctx.c_new_thread_exc(self._ctx, stack, threadlocal, exc)
        return res

    def kill_stack(self, stack):
        # type: (MuStackRefValue) -> None
        self._ctx.c_kill_stack(self._ctx, stack)

    def set_threadlocal(self, thread, threadlocal):
        # type: (MuThreadRefValue, MuRefValue) -> None
        self._ctx.c_set_threadlocal(self._ctx, thread, threadlocal)

    def get_threadlocal(self, thread):
        # type: (MuThreadRefValue) -> MuRefValue
        res = self._ctx.c_get_threadlocal(self._ctx, thread)
        return res

    def new_cursor(self, stack):
        # type: (MuStackRefValue) -> MuFCRefValue
        res = self._ctx.c_new_cursor(self._ctx, stack)
        return res

    def next_frame(self, cursor):
        # type: (MuFCRefValue) -> None
        self._ctx.c_next_frame(self._ctx, cursor)

    def copy_cursor(self, cursor):
        # type: (MuFCRefValue) -> MuFCRefValue
        res = self._ctx.c_copy_cursor(self._ctx, cursor)
        return res

    def close_cursor(self, cursor):
        # type: (MuFCRefValue) -> None
        self._ctx.c_close_cursor(self._ctx, cursor)

    def cur_func(self, cursor):
        # type: (MuFCRefValue) -> MuID
        res = self._ctx.c_cur_func(self._ctx, cursor)
        return res

    def cur_func_ver(self, cursor):
        # type: (MuFCRefValue) -> MuID
        res = self._ctx.c_cur_func_ver(self._ctx, cursor)
        return res

    def cur_inst(self, cursor):
        # type: (MuFCRefValue) -> MuID
        res = self._ctx.c_cur_inst(self._ctx, cursor)
        return res

    def dump_keepalives(self, cursor, results):
        # type: (MuFCRefValue, MuValuePtr) -> None
        self._ctx.c_dump_keepalives(self._ctx, cursor, results)

    def pop_frames_to(self, cursor):
        # type: (MuFCRefValue) -> None
        self._ctx.c_pop_frames_to(self._ctx, cursor)

    def push_frame(self, stack, func):
        # type: (MuStackRefValue, MuFuncRefValue) -> None
        self._ctx.c_push_frame(self._ctx, stack, func)

    def tr64_is_fp(self, value):
        # type: (MuTagRef64Value) -> bool
        res = bool(self._ctx.c_tr64_is_fp(self._ctx, value))
        return res

    def tr64_is_int(self, value):
        # type: (MuTagRef64Value) -> bool
        res = bool(self._ctx.c_tr64_is_int(self._ctx, value))
        return res

    def tr64_is_ref(self, value):
        # type: (MuTagRef64Value) -> bool
        res = bool(self._ctx.c_tr64_is_ref(self._ctx, value))
        return res

    def tr64_to_fp(self, value):
        # type: (MuTagRef64Value) -> MuDoubleValue
        res = self._ctx.c_tr64_to_fp(self._ctx, value)
        return res

    def tr64_to_int(self, value):
        # type: (MuTagRef64Value) -> MuIntValue
        res = self._ctx.c_tr64_to_int(self._ctx, value)
        return res

    def tr64_to_ref(self, value):
        # type: (MuTagRef64Value) -> MuRefValue
        res = self._ctx.c_tr64_to_ref(self._ctx, value)
        return res

    def tr64_to_tag(self, value):
        # type: (MuTagRef64Value) -> MuIntValue
        res = self._ctx.c_tr64_to_tag(self._ctx, value)
        return res

    def tr64_from_fp(self, value):
        # type: (MuDoubleValue) -> MuTagRef64Value
        res = self._ctx.c_tr64_from_fp(self._ctx, value)
        return res

    def tr64_from_int(self, value):
        # type: (MuIntValue) -> MuTagRef64Value
        res = self._ctx.c_tr64_from_int(self._ctx, value)
        return res

    def tr64_from_ref(self, ref, tag):
        # type: (MuRefValue, MuIntValue) -> MuTagRef64Value
        res = self._ctx.c_tr64_from_ref(self._ctx, ref, tag)
        return res

    def enable_watchpoint(self, wpid):
        # type: (MuWPID) -> None
        self._ctx.c_enable_watchpoint(self._ctx, wpid)

    def disable_watchpoint(self, wpid):
        # type: (MuWPID) -> None
        self._ctx.c_disable_watchpoint(self._ctx, wpid)

    def pin(self, loc):
        # type: (MuValue) -> MuUPtrValue
        res = self._ctx.c_pin(self._ctx, loc)
        return res

    def unpin(self, loc):
        # type: (MuValue) -> None
        self._ctx.c_unpin(self._ctx, loc)

    def get_addr(self, loc):
        # type: (MuValue) -> MuUPtrValue
        res = self._ctx.c_get_addr(self._ctx, loc)
        return res

    def expose(self, func, call_conv, cookie):
        # type: (MuFuncRefValue, MuFlag, MuIntValue) -> MuValue
        res = self._ctx.c_expose(self._ctx, func, call_conv, cookie)
        return res

    def unexpose(self, call_conv, value):
        # type: (MuFlag, MuValue) -> None
        self._ctx.c_unexpose(self._ctx, call_conv, value)

    def new_ir_builder(self):
        # type: () -> MuIRBuilder
        res = MuIRBuilder(self, self._ctx.c_new_ir_builder(self._ctx))
        return res

    def make_boot_image(self, whitelist, primordial_func, primordial_stack, primordial_threadlocal, sym_fields, sym_strings, reloc_fields, reloc_strings, output_file):
        # type: ([MuID], MuFuncRefValue, MuStackRefValue, MuRefValue, [MuIRefValue], [MuCString], [MuIRefValue], [MuCString], str) -> None
        whitelist_arr, whitelist_sz = lst2arr(MuID, whitelist)
        sym_fields_arr, sym_fields_sz = lst2arr(MuIRefValue, sym_fields)
        sym_strings_arr, sym_strings_sz = lst2arr(MuCString, sym_strings)
        reloc_fields_arr, reloc_fields_sz = lst2arr(MuIRefValue, reloc_fields)
        reloc_strings_arr, reloc_strings_sz = lst2arr(MuCString, reloc_strings)
        with rffi.scoped_str2charp(output_file) as output_file_buf:
            self._ctx.c_make_boot_image(self._ctx, whitelist_arr, whitelist_sz, primordial_func, primordial_stack, primordial_threadlocal, sym_fields_arr, sym_strings_arr, sym_strings_sz, reloc_fields_arr, reloc_strings_arr, reloc_strings_sz, output_file_buf)
            if whitelist_arr:
                lltype.free(whitelist_arr, flavor='raw')
            if sym_fields_arr:
                lltype.free(sym_fields_arr, flavor='raw')
            if sym_strings_arr:
                rffi.free_charpp(sym_strings_arr)
            if reloc_fields_arr:
                lltype.free(reloc_fields_arr, flavor='raw')
            if reloc_strings_arr:
                rffi.free_charpp(reloc_strings_arr)


class MuIRBuilder:
    def __init__(self, ctx, rffi_bldr_ptr):
        self._mu = ctx._mu
        self._bldr = rffi_bldr_ptr

    def load(self):
        # type: () -> None
        self._bldr.c_load(self._bldr)

    def abort(self):
        # type: () -> None
        self._bldr.c_abort(self._bldr)

    def gen_sym(self, name=None):
        # type: (str) -> MuID
        with rffi.scoped_str2charp(name) as name_buf:
            res = self._bldr.c_gen_sym(self._bldr, name_buf)
            return res

    def new_type_int(self, id, len):
        # type: (MuID, int) -> None
        len_c = rffi.cast(rffi.INT, len)
        self._bldr.c_new_type_int(self._bldr, id, len_c)

    def new_type_float(self, id):
        # type: (MuID) -> None
        self._bldr.c_new_type_float(self._bldr, id)

    def new_type_double(self, id):
        # type: (MuID) -> None
        self._bldr.c_new_type_double(self._bldr, id)

    def new_type_uptr(self, id, ty):
        # type: (MuID, MuTypeNode) -> None
        self._bldr.c_new_type_uptr(self._bldr, id, ty)

    def new_type_ufuncptr(self, id, sig):
        # type: (MuID, MuFuncSigNode) -> None
        self._bldr.c_new_type_ufuncptr(self._bldr, id, sig)

    def new_type_struct(self, id, fieldtys):
        # type: (MuID, [MuTypeNode]) -> None
        fieldtys_arr, fieldtys_sz = lst2arr(MuTypeNode, fieldtys)
        self._bldr.c_new_type_struct(self._bldr, id, fieldtys_arr, fieldtys_sz)
        if fieldtys_arr:
            lltype.free(fieldtys_arr, flavor='raw')

    def new_type_hybrid(self, id, fixedtys, varty):
        # type: (MuID, [MuTypeNode], MuTypeNode) -> None
        fixedtys_arr, fixedtys_sz = lst2arr(MuTypeNode, fixedtys)
        self._bldr.c_new_type_hybrid(self._bldr, id, fixedtys_arr, fixedtys_sz, varty)
        if fixedtys_arr:
            lltype.free(fixedtys_arr, flavor='raw')

    def new_type_array(self, id, elemty, len):
        # type: (MuID, MuTypeNode, int) -> None
        len_c = rffi.cast(rffi.ULONG, len)
        self._bldr.c_new_type_array(self._bldr, id, elemty, len_c)

    def new_type_vector(self, id, elemty, len):
        # type: (MuID, MuTypeNode, int) -> None
        len_c = rffi.cast(rffi.ULONG, len)
        self._bldr.c_new_type_vector(self._bldr, id, elemty, len_c)

    def new_type_void(self, id):
        # type: (MuID) -> None
        self._bldr.c_new_type_void(self._bldr, id)

    def new_type_ref(self, id, ty):
        # type: (MuID, MuTypeNode) -> None
        self._bldr.c_new_type_ref(self._bldr, id, ty)

    def new_type_iref(self, id, ty):
        # type: (MuID, MuTypeNode) -> None
        self._bldr.c_new_type_iref(self._bldr, id, ty)

    def new_type_weakref(self, id, ty):
        # type: (MuID, MuTypeNode) -> None
        self._bldr.c_new_type_weakref(self._bldr, id, ty)

    def new_type_funcref(self, id, sig):
        # type: (MuID, MuFuncSigNode) -> None
        self._bldr.c_new_type_funcref(self._bldr, id, sig)

    def new_type_tagref64(self, id):
        # type: (MuID) -> None
        self._bldr.c_new_type_tagref64(self._bldr, id)

    def new_type_threadref(self, id):
        # type: (MuID) -> None
        self._bldr.c_new_type_threadref(self._bldr, id)

    def new_type_stackref(self, id):
        # type: (MuID) -> None
        self._bldr.c_new_type_stackref(self._bldr, id)

    def new_type_framecursorref(self, id):
        # type: (MuID) -> None
        self._bldr.c_new_type_framecursorref(self._bldr, id)

    def new_type_irbuilderref(self, id):
        # type: (MuID) -> None
        self._bldr.c_new_type_irbuilderref(self._bldr, id)

    def new_funcsig(self, id, paramtys, rettys):
        # type: (MuID, [MuTypeNode], [MuTypeNode]) -> None
        paramtys_arr, paramtys_sz = lst2arr(MuTypeNode, paramtys)
        rettys_arr, rettys_sz = lst2arr(MuTypeNode, rettys)
        self._bldr.c_new_funcsig(self._bldr, id, paramtys_arr, paramtys_sz, rettys_arr, rettys_sz)
        if paramtys_arr:
            lltype.free(paramtys_arr, flavor='raw')
        if rettys_arr:
            lltype.free(rettys_arr, flavor='raw')

    def new_const_int(self, id, ty, value):
        # type: (MuID, MuTypeNode, int) -> None
        value_c = rffi.cast(rffi.ULONG, value)
        self._bldr.c_new_const_int(self._bldr, id, ty, value_c)

    def new_const_int_ex(self, id, ty, values):
        # type: (MuID, MuTypeNode, [rffi.ULONG]) -> None
        values_arr, values_sz = lst2arr(rffi.ULONG, values)
        self._bldr.c_new_const_int_ex(self._bldr, id, ty, values_arr, values_sz)
        if values_arr:
            lltype.free(values_arr, flavor='raw')

    def new_const_float(self, id, ty, value):
        # type: (MuID, MuTypeNode, float) -> None
        value_c = rffi.cast(rffi.FLOAT, value)
        self._bldr.c_new_const_float(self._bldr, id, ty, value_c)

    def new_const_double(self, id, ty, value):
        # type: (MuID, MuTypeNode, float) -> None
        value_c = rffi.cast(rffi.DOUBLE, value)
        self._bldr.c_new_const_double(self._bldr, id, ty, value_c)

    def new_const_null(self, id, ty):
        # type: (MuID, MuTypeNode) -> None
        self._bldr.c_new_const_null(self._bldr, id, ty)

    def new_const_seq(self, id, ty, elems):
        # type: (MuID, MuTypeNode, [MuGlobalVarNode]) -> None
        elems_arr, elems_sz = lst2arr(MuGlobalVarNode, elems)
        self._bldr.c_new_const_seq(self._bldr, id, ty, elems_arr, elems_sz)
        if elems_arr:
            lltype.free(elems_arr, flavor='raw')

    def new_const_extern(self, id, ty, symbol):
        # type: (MuID, MuTypeNode, str) -> None
        with rffi.scoped_str2charp(symbol) as symbol_buf:
            self._bldr.c_new_const_extern(self._bldr, id, ty, symbol_buf)

    def new_global_cell(self, id, ty):
        # type: (MuID, MuTypeNode) -> None
        self._bldr.c_new_global_cell(self._bldr, id, ty)

    def new_func(self, id, sig):
        # type: (MuID, MuFuncSigNode) -> None
        self._bldr.c_new_func(self._bldr, id, sig)

    def new_exp_func(self, id, func, callconv, cookie):
        # type: (MuID, MuFuncNode, MuFlag, MuConstNode) -> None
        self._bldr.c_new_exp_func(self._bldr, id, func, callconv, cookie)

    def new_func_ver(self, id, func, bbs):
        # type: (MuID, MuFuncNode, [MuBBNode]) -> None
        bbs_arr, bbs_sz = lst2arr(MuBBNode, bbs)
        self._bldr.c_new_func_ver(self._bldr, id, func, bbs_arr, bbs_sz)
        if bbs_arr:
            lltype.free(bbs_arr, flavor='raw')

    def new_bb(self, id, nor_param_ids, nor_param_types, exc_param_id, insts):
        # type: (MuID, [MuID], [MuTypeNode], MuID, [MuInstNode]) -> None
        nor_param_ids_arr, nor_param_ids_sz = lst2arr(MuID, nor_param_ids)
        nor_param_types_arr, nor_param_types_sz = lst2arr(MuTypeNode, nor_param_types)
        insts_arr, insts_sz = lst2arr(MuInstNode, insts)
        self._bldr.c_new_bb(self._bldr, id, nor_param_ids_arr, nor_param_types_arr, nor_param_types_sz, exc_param_id, insts_arr, insts_sz)
        if nor_param_ids_arr:
            lltype.free(nor_param_ids_arr, flavor='raw')
        if nor_param_types_arr:
            lltype.free(nor_param_types_arr, flavor='raw')
        if insts_arr:
            lltype.free(insts_arr, flavor='raw')

    def new_dest_clause(self, id, dest, vars):
        # type: (MuID, MuBBNode, [MuVarNode]) -> None
        vars_arr, vars_sz = lst2arr(MuVarNode, vars)
        self._bldr.c_new_dest_clause(self._bldr, id, dest, vars_arr, vars_sz)
        if vars_arr:
            lltype.free(vars_arr, flavor='raw')

    def new_exc_clause(self, id, nor, exc):
        # type: (MuID, MuDestClause, MuDestClause) -> None
        self._bldr.c_new_exc_clause(self._bldr, id, nor, exc)

    def new_keepalive_clause(self, id, vars):
        # type: (MuID, [MuLocalVarNode]) -> None
        vars_arr, vars_sz = lst2arr(MuLocalVarNode, vars)
        self._bldr.c_new_keepalive_clause(self._bldr, id, vars_arr, vars_sz)
        if vars_arr:
            lltype.free(vars_arr, flavor='raw')

    def new_csc_ret_with(self, id, rettys):
        # type: (MuID, [MuTypeNode]) -> None
        rettys_arr, rettys_sz = lst2arr(MuTypeNode, rettys)
        self._bldr.c_new_csc_ret_with(self._bldr, id, rettys_arr, rettys_sz)
        if rettys_arr:
            lltype.free(rettys_arr, flavor='raw')

    def new_csc_kill_old(self, id):
        # type: (MuID) -> None
        self._bldr.c_new_csc_kill_old(self._bldr, id)

    def new_nsc_pass_values(self, id, tys, vars):
        # type: (MuID, [MuTypeNode], [MuVarNode]) -> None
        tys_arr, tys_sz = lst2arr(MuTypeNode, tys)
        vars_arr, vars_sz = lst2arr(MuVarNode, vars)
        self._bldr.c_new_nsc_pass_values(self._bldr, id, tys_arr, vars_arr, vars_sz)
        if tys_arr:
            lltype.free(tys_arr, flavor='raw')
        if vars_arr:
            lltype.free(vars_arr, flavor='raw')

    def new_nsc_throw_exc(self, id, exc):
        # type: (MuID, MuVarNode) -> None
        self._bldr.c_new_nsc_throw_exc(self._bldr, id, exc)

    def new_binop(self, id, result_id, optr, ty, opnd1, opnd2, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, MuFlag, MuTypeNode, MuVarNode, MuVarNode, MuExcClause) -> None
        self._bldr.c_new_binop(self._bldr, id, result_id, optr, ty, opnd1, opnd2, exc_clause)

    def new_binop_with_status(self, id, result_id, status_result_ids, optr, status_flags, ty, opnd1, opnd2, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, [MuID], MuFlag, MuBinOpStatus, MuTypeNode, MuVarNode, MuVarNode, MuExcClause) -> None
        status_result_ids_arr, status_result_ids_sz = lst2arr(MuID, status_result_ids)
        self._bldr.c_new_binop_with_status(self._bldr, id, result_id, status_result_ids_arr, status_result_ids_sz, optr, status_flags, ty, opnd1, opnd2, exc_clause)
        if status_result_ids_arr:
            lltype.free(status_result_ids_arr, flavor='raw')

    def new_cmp(self, id, result_id, optr, ty, opnd1, opnd2):
        # type: (MuID, MuID, MuFlag, MuTypeNode, MuVarNode, MuVarNode) -> None
        self._bldr.c_new_cmp(self._bldr, id, result_id, optr, ty, opnd1, opnd2)

    def new_conv(self, id, result_id, optr, from_ty, to_ty, opnd):
        # type: (MuID, MuID, MuFlag, MuTypeNode, MuTypeNode, MuVarNode) -> None
        self._bldr.c_new_conv(self._bldr, id, result_id, optr, from_ty, to_ty, opnd)

    def new_select(self, id, result_id, cond_ty, opnd_ty, cond, if_true, if_false):
        # type: (MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> None
        self._bldr.c_new_select(self._bldr, id, result_id, cond_ty, opnd_ty, cond, if_true, if_false)

    def new_branch(self, id, dest):
        # type: (MuID, MuDestClause) -> None
        self._bldr.c_new_branch(self._bldr, id, dest)

    def new_branch2(self, id, cond, if_true, if_false):
        # type: (MuID, MuVarNode, MuDestClause, MuDestClause) -> None
        self._bldr.c_new_branch2(self._bldr, id, cond, if_true, if_false)

    def new_switch(self, id, opnd_ty, opnd, default_dest, cases, dests):
        # type: (MuID, MuTypeNode, MuVarNode, MuDestClause, [MuConstNode], [MuDestClause]) -> None
        cases_arr, cases_sz = lst2arr(MuConstNode, cases)
        dests_arr, dests_sz = lst2arr(MuDestClause, dests)
        self._bldr.c_new_switch(self._bldr, id, opnd_ty, opnd, default_dest, cases_arr, dests_arr, dests_sz)
        if cases_arr:
            lltype.free(cases_arr, flavor='raw')
        if dests_arr:
            lltype.free(dests_arr, flavor='raw')

    def new_call(self, id, result_ids, sig, callee, args, exc_clause=MU_NO_ID, keepalive_clause=MU_NO_ID):
        # type: (MuID, [MuID], MuFuncSigNode, MuVarNode, [MuVarNode], MuExcClause, MuKeepaliveClause) -> None
        result_ids_arr, result_ids_sz = lst2arr(MuID, result_ids)
        args_arr, args_sz = lst2arr(MuVarNode, args)
        self._bldr.c_new_call(self._bldr, id, result_ids_arr, result_ids_sz, sig, callee, args_arr, args_sz, exc_clause, keepalive_clause)
        if result_ids_arr:
            lltype.free(result_ids_arr, flavor='raw')
        if args_arr:
            lltype.free(args_arr, flavor='raw')

    def new_tailcall(self, id, sig, callee, args):
        # type: (MuID, MuFuncSigNode, MuVarNode, [MuVarNode]) -> None
        args_arr, args_sz = lst2arr(MuVarNode, args)
        self._bldr.c_new_tailcall(self._bldr, id, sig, callee, args_arr, args_sz)
        if args_arr:
            lltype.free(args_arr, flavor='raw')

    def new_ret(self, id, rvs):
        # type: (MuID, [MuVarNode]) -> None
        rvs_arr, rvs_sz = lst2arr(MuVarNode, rvs)
        self._bldr.c_new_ret(self._bldr, id, rvs_arr, rvs_sz)
        if rvs_arr:
            lltype.free(rvs_arr, flavor='raw')

    def new_throw(self, id, exc):
        # type: (MuID, MuVarNode) -> None
        self._bldr.c_new_throw(self._bldr, id, exc)

    def new_extractvalue(self, id, result_id, strty, index, opnd):
        # type: (MuID, MuID, MuTypeNode, int, MuVarNode) -> None
        index_c = rffi.cast(rffi.INT, index)
        self._bldr.c_new_extractvalue(self._bldr, id, result_id, strty, index_c, opnd)

    def new_insertvalue(self, id, result_id, strty, index, opnd, newval):
        # type: (MuID, MuID, MuTypeNode, int, MuVarNode, MuVarNode) -> None
        index_c = rffi.cast(rffi.INT, index)
        self._bldr.c_new_insertvalue(self._bldr, id, result_id, strty, index_c, opnd, newval)

    def new_extractelement(self, id, result_id, seqty, indty, opnd, index):
        # type: (MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> None
        self._bldr.c_new_extractelement(self._bldr, id, result_id, seqty, indty, opnd, index)

    def new_insertelement(self, id, result_id, seqty, indty, opnd, index, newval):
        # type: (MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> None
        self._bldr.c_new_insertelement(self._bldr, id, result_id, seqty, indty, opnd, index, newval)

    def new_shufflevector(self, id, result_id, vecty, maskty, vec1, vec2, mask):
        # type: (MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> None
        self._bldr.c_new_shufflevector(self._bldr, id, result_id, vecty, maskty, vec1, vec2, mask)

    def new_new(self, id, result_id, allocty, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, MuTypeNode, MuExcClause) -> None
        self._bldr.c_new_new(self._bldr, id, result_id, allocty, exc_clause)

    def new_newhybrid(self, id, result_id, allocty, lenty, length, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuExcClause) -> None
        self._bldr.c_new_newhybrid(self._bldr, id, result_id, allocty, lenty, length, exc_clause)

    def new_alloca(self, id, result_id, allocty, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, MuTypeNode, MuExcClause) -> None
        self._bldr.c_new_alloca(self._bldr, id, result_id, allocty, exc_clause)

    def new_allocahybrid(self, id, result_id, allocty, lenty, length, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuExcClause) -> None
        self._bldr.c_new_allocahybrid(self._bldr, id, result_id, allocty, lenty, length, exc_clause)

    def new_getiref(self, id, result_id, refty, opnd):
        # type: (MuID, MuID, MuTypeNode, MuVarNode) -> None
        self._bldr.c_new_getiref(self._bldr, id, result_id, refty, opnd)

    def new_getfieldiref(self, id, result_id, is_ptr, refty, index, opnd):
        # type: (MuID, MuID, bool, MuTypeNode, int, MuVarNode) -> None
        is_ptr_c = rffi.cast(MuBool, is_ptr)
        index_c = rffi.cast(rffi.INT, index)
        self._bldr.c_new_getfieldiref(self._bldr, id, result_id, is_ptr_c, refty, index_c, opnd)

    def new_getelemiref(self, id, result_id, is_ptr, refty, indty, opnd, index):
        # type: (MuID, MuID, bool, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> None
        is_ptr_c = rffi.cast(MuBool, is_ptr)
        self._bldr.c_new_getelemiref(self._bldr, id, result_id, is_ptr_c, refty, indty, opnd, index)

    def new_shiftiref(self, id, result_id, is_ptr, refty, offty, opnd, offset):
        # type: (MuID, MuID, bool, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> None
        is_ptr_c = rffi.cast(MuBool, is_ptr)
        self._bldr.c_new_shiftiref(self._bldr, id, result_id, is_ptr_c, refty, offty, opnd, offset)

    def new_getvarpartiref(self, id, result_id, is_ptr, refty, opnd):
        # type: (MuID, MuID, bool, MuTypeNode, MuVarNode) -> None
        is_ptr_c = rffi.cast(MuBool, is_ptr)
        self._bldr.c_new_getvarpartiref(self._bldr, id, result_id, is_ptr_c, refty, opnd)

    def new_load(self, id, result_id, is_ptr, ord, refty, loc, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, bool, MuFlag, MuTypeNode, MuVarNode, MuExcClause) -> None
        is_ptr_c = rffi.cast(MuBool, is_ptr)
        self._bldr.c_new_load(self._bldr, id, result_id, is_ptr_c, ord, refty, loc, exc_clause)

    def new_store(self, id, is_ptr, ord, refty, loc, newval, exc_clause=MU_NO_ID):
        # type: (MuID, bool, MuFlag, MuTypeNode, MuVarNode, MuVarNode, MuExcClause) -> None
        is_ptr_c = rffi.cast(MuBool, is_ptr)
        self._bldr.c_new_store(self._bldr, id, is_ptr_c, ord, refty, loc, newval, exc_clause)

    def new_cmpxchg(self, id, value_result_id, succ_result_id, is_ptr, is_weak, ord_succ, ord_fail, refty, loc, expected, desired, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, MuID, bool, bool, MuFlag, MuFlag, MuTypeNode, MuVarNode, MuVarNode, MuVarNode, MuExcClause) -> None
        is_ptr_c = rffi.cast(MuBool, is_ptr)
        is_weak_c = rffi.cast(MuBool, is_weak)
        self._bldr.c_new_cmpxchg(self._bldr, id, value_result_id, succ_result_id, is_ptr_c, is_weak_c, ord_succ, ord_fail, refty, loc, expected, desired, exc_clause)

    def new_atomicrmw(self, id, result_id, is_ptr, ord, optr, ref_ty, loc, opnd, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, bool, MuFlag, MuFlag, MuTypeNode, MuVarNode, MuVarNode, MuExcClause) -> None
        is_ptr_c = rffi.cast(MuBool, is_ptr)
        self._bldr.c_new_atomicrmw(self._bldr, id, result_id, is_ptr_c, ord, optr, ref_ty, loc, opnd, exc_clause)

    def new_fence(self, id, ord):
        # type: (MuID, MuFlag) -> None
        self._bldr.c_new_fence(self._bldr, id, ord)

    def new_trap(self, id, result_ids, rettys, exc_clause=MU_NO_ID, keepalive_clause=MU_NO_ID):
        # type: (MuID, [MuID], [MuTypeNode], MuExcClause, MuKeepaliveClause) -> None
        result_ids_arr, result_ids_sz = lst2arr(MuID, result_ids)
        rettys_arr, rettys_sz = lst2arr(MuTypeNode, rettys)
        self._bldr.c_new_trap(self._bldr, id, result_ids_arr, rettys_arr, rettys_sz, exc_clause, keepalive_clause)
        if result_ids_arr:
            lltype.free(result_ids_arr, flavor='raw')
        if rettys_arr:
            lltype.free(rettys_arr, flavor='raw')

    def new_watchpoint(self, id, wpid, result_ids, rettys, dis, ena, exc=MU_NO_ID, keepalive_clause=MU_NO_ID):
        # type: (MuID, MuWPID, [MuID], [MuTypeNode], MuDestClause, MuDestClause, MuDestClause, MuKeepaliveClause) -> None
        result_ids_arr, result_ids_sz = lst2arr(MuID, result_ids)
        rettys_arr, rettys_sz = lst2arr(MuTypeNode, rettys)
        self._bldr.c_new_watchpoint(self._bldr, id, wpid, result_ids_arr, rettys_arr, rettys_sz, dis, ena, exc, keepalive_clause)
        if result_ids_arr:
            lltype.free(result_ids_arr, flavor='raw')
        if rettys_arr:
            lltype.free(rettys_arr, flavor='raw')

    def new_wpbranch(self, id, wpid, dis, ena):
        # type: (MuID, MuWPID, MuDestClause, MuDestClause) -> None
        self._bldr.c_new_wpbranch(self._bldr, id, wpid, dis, ena)

    def new_ccall(self, id, result_ids, callconv, callee_ty, sig, callee, args, exc_clause=MU_NO_ID, keepalive_clause=MU_NO_ID):
        # type: (MuID, [MuID], MuFlag, MuTypeNode, MuFuncSigNode, MuVarNode, [MuVarNode], MuExcClause, MuKeepaliveClause) -> None
        result_ids_arr, result_ids_sz = lst2arr(MuID, result_ids)
        args_arr, args_sz = lst2arr(MuVarNode, args)
        self._bldr.c_new_ccall(self._bldr, id, result_ids_arr, result_ids_sz, callconv, callee_ty, sig, callee, args_arr, args_sz, exc_clause, keepalive_clause)
        if result_ids_arr:
            lltype.free(result_ids_arr, flavor='raw')
        if args_arr:
            lltype.free(args_arr, flavor='raw')

    def new_newthread(self, id, result_id, stack, threadlocal, new_stack_clause, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, MuVarNode, MuVarNode, MuNewStackClause, MuExcClause) -> None
        self._bldr.c_new_newthread(self._bldr, id, result_id, stack, threadlocal, new_stack_clause, exc_clause)

    def new_swapstack(self, id, result_ids, swappee, cur_stack_clause, new_stack_clause, exc_clause=MU_NO_ID, keepalive_clause=MU_NO_ID):
        # type: (MuID, [MuID], MuVarNode, MuCurStackClause, MuNewStackClause, MuExcClause, MuKeepaliveClause) -> None
        result_ids_arr, result_ids_sz = lst2arr(MuID, result_ids)
        self._bldr.c_new_swapstack(self._bldr, id, result_ids_arr, result_ids_sz, swappee, cur_stack_clause, new_stack_clause, exc_clause, keepalive_clause)
        if result_ids_arr:
            lltype.free(result_ids_arr, flavor='raw')

    def new_comminst(self, id, result_ids, opcode, flags, tys, sigs, args, exc_clause=MU_NO_ID, keepalive_clause=MU_NO_ID):
        # type: (MuID, [MuID], MuFlag, [MuFlag], [MuTypeNode], [MuFuncSigNode], [MuVarNode], MuExcClause, MuKeepaliveClause) -> None
        result_ids_arr, result_ids_sz = lst2arr(MuID, result_ids)
        flags_arr, flags_sz = lst2arr(MuFlag, flags)
        tys_arr, tys_sz = lst2arr(MuTypeNode, tys)
        sigs_arr, sigs_sz = lst2arr(MuFuncSigNode, sigs)
        args_arr, args_sz = lst2arr(MuVarNode, args)
        self._bldr.c_new_comminst(self._bldr, id, result_ids_arr, result_ids_sz, opcode, flags_arr, flags_sz, tys_arr, tys_sz, sigs_arr, sigs_sz, args_arr, args_sz, exc_clause, keepalive_clause)
        if result_ids_arr:
            lltype.free(result_ids_arr, flavor='raw')
        if flags_arr:
            lltype.free(flags_arr, flavor='raw')
        if tys_arr:
            lltype.free(tys_arr, flavor='raw')
        if sigs_arr:
            lltype.free(sigs_arr, flavor='raw')
        if args_arr:
            lltype.free(args_arr, flavor='raw')


# -------------------------------------------------------------------------------------------------------
# Structs
_MuVM.become(rffi.CStruct(
    'MuVM',
    ('header', rffi.VOIDP),
    ('new_context', rffi.CCallback([_MuVMPtr], _MuCtxPtr)),
    ('id_of', rffi.CCallback([_MuVMPtr, MuName], MuID)),
    ('name_of', rffi.CCallback([_MuVMPtr, MuID], MuName)),
    ('set_trap_handler', rffi.CCallback([_MuVMPtr, MuTrapHandler, MuCPtr], lltype.Void)),
    ('compile_to_sharedlib', rffi.CCallback([_MuVMPtr, MuCString, MuCStringPtr, MuArraySize], lltype.Void)),
    ('current_thread_as_mu_thread', rffi.CCallback([_MuVMPtr, MuCPtr], lltype.Void)),
))
_MuCtx.become(rffi.CStruct(
    'MuCtx',
    ('header', rffi.VOIDP),
    ('id_of', rffi.CCallback([_MuCtxPtr, MuName], MuID)),
    ('name_of', rffi.CCallback([_MuCtxPtr, MuID], MuName)),
    ('close_context', rffi.CCallback([_MuCtxPtr], lltype.Void)),
    ('load_bundle', rffi.CCallback([_MuCtxPtr, rffi.CCHARP, MuArraySize], lltype.Void)),
    ('load_hail', rffi.CCallback([_MuCtxPtr, rffi.CCHARP, MuArraySize], lltype.Void)),
    ('handle_from_sint8', rffi.CCallback([_MuCtxPtr, rffi.CHAR, rffi.INT], MuIntValue)),
    ('handle_from_uint8', rffi.CCallback([_MuCtxPtr, rffi.UCHAR, rffi.INT], MuIntValue)),
    ('handle_from_sint16', rffi.CCallback([_MuCtxPtr, rffi.SHORT, rffi.INT], MuIntValue)),
    ('handle_from_uint16', rffi.CCallback([_MuCtxPtr, rffi.USHORT, rffi.INT], MuIntValue)),
    ('handle_from_sint32', rffi.CCallback([_MuCtxPtr, rffi.INT, rffi.INT], MuIntValue)),
    ('handle_from_uint32', rffi.CCallback([_MuCtxPtr, rffi.UINT, rffi.INT], MuIntValue)),
    ('handle_from_sint64', rffi.CCallback([_MuCtxPtr, rffi.LONG, rffi.INT], MuIntValue)),
    ('handle_from_uint64', rffi.CCallback([_MuCtxPtr, rffi.ULONG, rffi.INT], MuIntValue)),
    ('handle_from_uint64s', rffi.CCallback([_MuCtxPtr, rffi.ULONGP, MuArraySize, rffi.INT], MuIntValue)),
    ('handle_from_float', rffi.CCallback([_MuCtxPtr, rffi.FLOAT], MuFloatValue)),
    ('handle_from_double', rffi.CCallback([_MuCtxPtr, rffi.DOUBLE], MuDoubleValue)),
    ('handle_from_ptr', rffi.CCallback([_MuCtxPtr, MuID, MuCPtr], MuUPtrValue)),
    ('handle_from_fp', rffi.CCallback([_MuCtxPtr, MuID, MuCFP], MuUFPValue)),
    ('handle_to_sint8', rffi.CCallback([_MuCtxPtr, MuIntValue], rffi.CHAR)),
    ('handle_to_uint8', rffi.CCallback([_MuCtxPtr, MuIntValue], rffi.UCHAR)),
    ('handle_to_sint16', rffi.CCallback([_MuCtxPtr, MuIntValue], rffi.SHORT)),
    ('handle_to_uint16', rffi.CCallback([_MuCtxPtr, MuIntValue], rffi.USHORT)),
    ('handle_to_sint32', rffi.CCallback([_MuCtxPtr, MuIntValue], rffi.INT)),
    ('handle_to_uint32', rffi.CCallback([_MuCtxPtr, MuIntValue], rffi.UINT)),
    ('handle_to_sint64', rffi.CCallback([_MuCtxPtr, MuIntValue], rffi.LONG)),
    ('handle_to_uint64', rffi.CCallback([_MuCtxPtr, MuIntValue], rffi.ULONG)),
    ('handle_to_float', rffi.CCallback([_MuCtxPtr, MuFloatValue], rffi.FLOAT)),
    ('handle_to_double', rffi.CCallback([_MuCtxPtr, MuDoubleValue], rffi.DOUBLE)),
    ('handle_to_ptr', rffi.CCallback([_MuCtxPtr, MuUPtrValue], MuCPtr)),
    ('handle_to_fp', rffi.CCallback([_MuCtxPtr, MuUFPValue], MuCFP)),
    ('handle_from_const', rffi.CCallback([_MuCtxPtr, MuID], MuValue)),
    ('handle_from_global', rffi.CCallback([_MuCtxPtr, MuID], MuIRefValue)),
    ('handle_from_func', rffi.CCallback([_MuCtxPtr, MuID], MuFuncRefValue)),
    ('handle_from_expose', rffi.CCallback([_MuCtxPtr, MuID], MuValue)),
    ('delete_value', rffi.CCallback([_MuCtxPtr, MuValue], lltype.Void)),
    ('ref_eq', rffi.CCallback([_MuCtxPtr, MuGenRefValue, MuGenRefValue], MuBool)),
    ('ref_ult', rffi.CCallback([_MuCtxPtr, MuIRefValue, MuIRefValue], MuBool)),
    ('extract_value', rffi.CCallback([_MuCtxPtr, MuStructValue, rffi.INT], MuValue)),
    ('insert_value', rffi.CCallback([_MuCtxPtr, MuStructValue, rffi.INT, MuValue], MuStructValue)),
    ('extract_element', rffi.CCallback([_MuCtxPtr, MuSeqValue, MuIntValue], MuValue)),
    ('insert_element', rffi.CCallback([_MuCtxPtr, MuSeqValue, MuIntValue, MuValue], MuSeqValue)),
    ('new_fixed', rffi.CCallback([_MuCtxPtr, MuID], MuRefValue)),
    ('new_hybrid', rffi.CCallback([_MuCtxPtr, MuID, MuIntValue], MuRefValue)),
    ('refcast', rffi.CCallback([_MuCtxPtr, MuGenRefValue, MuID], MuGenRefValue)),
    ('get_iref', rffi.CCallback([_MuCtxPtr, MuRefValue], MuIRefValue)),
    ('get_field_iref', rffi.CCallback([_MuCtxPtr, MuIRefValue, rffi.INT], MuIRefValue)),
    ('get_elem_iref', rffi.CCallback([_MuCtxPtr, MuIRefValue, MuIntValue], MuIRefValue)),
    ('shift_iref', rffi.CCallback([_MuCtxPtr, MuIRefValue, MuIntValue], MuIRefValue)),
    ('get_var_part_iref', rffi.CCallback([_MuCtxPtr, MuIRefValue], MuIRefValue)),
    ('load', rffi.CCallback([_MuCtxPtr, MuFlag, MuIRefValue], MuValue)),
    ('store', rffi.CCallback([_MuCtxPtr, MuFlag, MuIRefValue, MuValue], lltype.Void)),
    ('cmpxchg', rffi.CCallback([_MuCtxPtr, MuFlag, MuFlag, MuBool, MuIRefValue, MuValue, MuValue, MuBoolPtr], MuValue)),
    ('atomicrmw', rffi.CCallback([_MuCtxPtr, MuFlag, MuFlag, MuIRefValue, MuValue], MuValue)),
    ('fence', rffi.CCallback([_MuCtxPtr, MuFlag], lltype.Void)),
    ('new_stack', rffi.CCallback([_MuCtxPtr, MuFuncRefValue], MuStackRefValue)),
    ('new_thread_nor', rffi.CCallback([_MuCtxPtr, MuStackRefValue, MuRefValue, MuValuePtr, MuArraySize], MuThreadRefValue)),
    ('new_thread_exc', rffi.CCallback([_MuCtxPtr, MuStackRefValue, MuRefValue, MuRefValue], MuThreadRefValue)),
    ('kill_stack', rffi.CCallback([_MuCtxPtr, MuStackRefValue], lltype.Void)),
    ('set_threadlocal', rffi.CCallback([_MuCtxPtr, MuThreadRefValue, MuRefValue], lltype.Void)),
    ('get_threadlocal', rffi.CCallback([_MuCtxPtr, MuThreadRefValue], MuRefValue)),
    ('new_cursor', rffi.CCallback([_MuCtxPtr, MuStackRefValue], MuFCRefValue)),
    ('next_frame', rffi.CCallback([_MuCtxPtr, MuFCRefValue], lltype.Void)),
    ('copy_cursor', rffi.CCallback([_MuCtxPtr, MuFCRefValue], MuFCRefValue)),
    ('close_cursor', rffi.CCallback([_MuCtxPtr, MuFCRefValue], lltype.Void)),
    ('cur_func', rffi.CCallback([_MuCtxPtr, MuFCRefValue], MuID)),
    ('cur_func_ver', rffi.CCallback([_MuCtxPtr, MuFCRefValue], MuID)),
    ('cur_inst', rffi.CCallback([_MuCtxPtr, MuFCRefValue], MuID)),
    ('dump_keepalives', rffi.CCallback([_MuCtxPtr, MuFCRefValue, MuValuePtr], lltype.Void)),
    ('pop_frames_to', rffi.CCallback([_MuCtxPtr, MuFCRefValue], lltype.Void)),
    ('push_frame', rffi.CCallback([_MuCtxPtr, MuStackRefValue, MuFuncRefValue], lltype.Void)),
    ('tr64_is_fp', rffi.CCallback([_MuCtxPtr, MuTagRef64Value], MuBool)),
    ('tr64_is_int', rffi.CCallback([_MuCtxPtr, MuTagRef64Value], MuBool)),
    ('tr64_is_ref', rffi.CCallback([_MuCtxPtr, MuTagRef64Value], MuBool)),
    ('tr64_to_fp', rffi.CCallback([_MuCtxPtr, MuTagRef64Value], MuDoubleValue)),
    ('tr64_to_int', rffi.CCallback([_MuCtxPtr, MuTagRef64Value], MuIntValue)),
    ('tr64_to_ref', rffi.CCallback([_MuCtxPtr, MuTagRef64Value], MuRefValue)),
    ('tr64_to_tag', rffi.CCallback([_MuCtxPtr, MuTagRef64Value], MuIntValue)),
    ('tr64_from_fp', rffi.CCallback([_MuCtxPtr, MuDoubleValue], MuTagRef64Value)),
    ('tr64_from_int', rffi.CCallback([_MuCtxPtr, MuIntValue], MuTagRef64Value)),
    ('tr64_from_ref', rffi.CCallback([_MuCtxPtr, MuRefValue, MuIntValue], MuTagRef64Value)),
    ('enable_watchpoint', rffi.CCallback([_MuCtxPtr, MuWPID], lltype.Void)),
    ('disable_watchpoint', rffi.CCallback([_MuCtxPtr, MuWPID], lltype.Void)),
    ('pin', rffi.CCallback([_MuCtxPtr, MuValue], MuUPtrValue)),
    ('unpin', rffi.CCallback([_MuCtxPtr, MuValue], lltype.Void)),
    ('get_addr', rffi.CCallback([_MuCtxPtr, MuValue], MuUPtrValue)),
    ('expose', rffi.CCallback([_MuCtxPtr, MuFuncRefValue, MuFlag, MuIntValue], MuValue)),
    ('unexpose', rffi.CCallback([_MuCtxPtr, MuFlag, MuValue], lltype.Void)),
    ('new_ir_builder', rffi.CCallback([_MuCtxPtr], _MuIRBuilderPtr)),
    ('make_boot_image', rffi.CCallback([_MuCtxPtr, MuIDPtr, MuArraySize, MuFuncRefValue, MuStackRefValue, MuRefValue, MuIRefValuePtr, MuCStringPtr, MuArraySize, MuIRefValuePtr, MuCStringPtr, MuArraySize, MuCString], lltype.Void)),
))
_MuIRBuilder.become(rffi.CStruct(
    'MuIRBuilder',
    ('header', rffi.VOIDP),
    ('load', rffi.CCallback([_MuIRBuilderPtr], lltype.Void)),
    ('abort', rffi.CCallback([_MuIRBuilderPtr], lltype.Void)),
    ('gen_sym', rffi.CCallback([_MuIRBuilderPtr, MuCString], MuID)),
    ('new_type_int', rffi.CCallback([_MuIRBuilderPtr, MuID, rffi.INT], lltype.Void)),
    ('new_type_float', rffi.CCallback([_MuIRBuilderPtr, MuID], lltype.Void)),
    ('new_type_double', rffi.CCallback([_MuIRBuilderPtr, MuID], lltype.Void)),
    ('new_type_uptr', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNode], lltype.Void)),
    ('new_type_ufuncptr', rffi.CCallback([_MuIRBuilderPtr, MuID, MuFuncSigNode], lltype.Void)),
    ('new_type_struct', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNodePtr, MuArraySize], lltype.Void)),
    ('new_type_hybrid', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNodePtr, MuArraySize, MuTypeNode], lltype.Void)),
    ('new_type_array', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNode, rffi.ULONG], lltype.Void)),
    ('new_type_vector', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNode, rffi.ULONG], lltype.Void)),
    ('new_type_void', rffi.CCallback([_MuIRBuilderPtr, MuID], lltype.Void)),
    ('new_type_ref', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNode], lltype.Void)),
    ('new_type_iref', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNode], lltype.Void)),
    ('new_type_weakref', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNode], lltype.Void)),
    ('new_type_funcref', rffi.CCallback([_MuIRBuilderPtr, MuID, MuFuncSigNode], lltype.Void)),
    ('new_type_tagref64', rffi.CCallback([_MuIRBuilderPtr, MuID], lltype.Void)),
    ('new_type_threadref', rffi.CCallback([_MuIRBuilderPtr, MuID], lltype.Void)),
    ('new_type_stackref', rffi.CCallback([_MuIRBuilderPtr, MuID], lltype.Void)),
    ('new_type_framecursorref', rffi.CCallback([_MuIRBuilderPtr, MuID], lltype.Void)),
    ('new_type_irbuilderref', rffi.CCallback([_MuIRBuilderPtr, MuID], lltype.Void)),
    ('new_funcsig', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNodePtr, MuArraySize, MuTypeNodePtr, MuArraySize], lltype.Void)),
    ('new_const_int', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNode, rffi.ULONG], lltype.Void)),
    ('new_const_int_ex', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNode, rffi.ULONGP, MuArraySize], lltype.Void)),
    ('new_const_float', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNode, rffi.FLOAT], lltype.Void)),
    ('new_const_double', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNode, rffi.DOUBLE], lltype.Void)),
    ('new_const_null', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNode], lltype.Void)),
    ('new_const_seq', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNode, MuGlobalVarNodePtr, MuArraySize], lltype.Void)),
    ('new_const_extern', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNode, MuCString], lltype.Void)),
    ('new_global_cell', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNode], lltype.Void)),
    ('new_func', rffi.CCallback([_MuIRBuilderPtr, MuID, MuFuncSigNode], lltype.Void)),
    ('new_exp_func', rffi.CCallback([_MuIRBuilderPtr, MuID, MuFuncNode, MuFlag, MuConstNode], lltype.Void)),
    ('new_func_ver', rffi.CCallback([_MuIRBuilderPtr, MuID, MuFuncNode, MuBBNodePtr, MuArraySize], lltype.Void)),
    ('new_bb', rffi.CCallback([_MuIRBuilderPtr, MuID, MuIDPtr, MuTypeNodePtr, MuArraySize, MuID, MuInstNodePtr, MuArraySize], lltype.Void)),
    ('new_dest_clause', rffi.CCallback([_MuIRBuilderPtr, MuID, MuBBNode, MuVarNodePtr, MuArraySize], lltype.Void)),
    ('new_exc_clause', rffi.CCallback([_MuIRBuilderPtr, MuID, MuDestClause, MuDestClause], lltype.Void)),
    ('new_keepalive_clause', rffi.CCallback([_MuIRBuilderPtr, MuID, MuLocalVarNodePtr, MuArraySize], lltype.Void)),
    ('new_csc_ret_with', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNodePtr, MuArraySize], lltype.Void)),
    ('new_csc_kill_old', rffi.CCallback([_MuIRBuilderPtr, MuID], lltype.Void)),
    ('new_nsc_pass_values', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNodePtr, MuVarNodePtr, MuArraySize], lltype.Void)),
    ('new_nsc_throw_exc', rffi.CCallback([_MuIRBuilderPtr, MuID, MuVarNode], lltype.Void)),
    ('new_binop', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuFlag, MuTypeNode, MuVarNode, MuVarNode, MuExcClause], lltype.Void)),
    ('new_binop_with_status', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuIDPtr, MuArraySize, MuFlag, MuFlag, MuTypeNode, MuVarNode, MuVarNode, MuExcClause], lltype.Void)),
    ('new_cmp', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuFlag, MuTypeNode, MuVarNode, MuVarNode], lltype.Void)),
    ('new_conv', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuFlag, MuTypeNode, MuTypeNode, MuVarNode], lltype.Void)),
    ('new_select', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode], lltype.Void)),
    ('new_branch', rffi.CCallback([_MuIRBuilderPtr, MuID, MuDestClause], lltype.Void)),
    ('new_branch2', rffi.CCallback([_MuIRBuilderPtr, MuID, MuVarNode, MuDestClause, MuDestClause], lltype.Void)),
    ('new_switch', rffi.CCallback([_MuIRBuilderPtr, MuID, MuTypeNode, MuVarNode, MuDestClause, MuConstNodePtr, MuDestClausePtr, MuArraySize], lltype.Void)),
    ('new_call', rffi.CCallback([_MuIRBuilderPtr, MuID, MuIDPtr, MuArraySize, MuFuncSigNode, MuVarNode, MuVarNodePtr, MuArraySize, MuExcClause, MuKeepaliveClause], lltype.Void)),
    ('new_tailcall', rffi.CCallback([_MuIRBuilderPtr, MuID, MuFuncSigNode, MuVarNode, MuVarNodePtr, MuArraySize], lltype.Void)),
    ('new_ret', rffi.CCallback([_MuIRBuilderPtr, MuID, MuVarNodePtr, MuArraySize], lltype.Void)),
    ('new_throw', rffi.CCallback([_MuIRBuilderPtr, MuID, MuVarNode], lltype.Void)),
    ('new_extractvalue', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuTypeNode, rffi.INT, MuVarNode], lltype.Void)),
    ('new_insertvalue', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuTypeNode, rffi.INT, MuVarNode, MuVarNode], lltype.Void)),
    ('new_extractelement', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode], lltype.Void)),
    ('new_insertelement', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode], lltype.Void)),
    ('new_shufflevector', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode], lltype.Void)),
    ('new_new', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuTypeNode, MuExcClause], lltype.Void)),
    ('new_newhybrid', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuExcClause], lltype.Void)),
    ('new_alloca', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuTypeNode, MuExcClause], lltype.Void)),
    ('new_allocahybrid', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuExcClause], lltype.Void)),
    ('new_getiref', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuTypeNode, MuVarNode], lltype.Void)),
    ('new_getfieldiref', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuBool, MuTypeNode, rffi.INT, MuVarNode], lltype.Void)),
    ('new_getelemiref', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuBool, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode], lltype.Void)),
    ('new_shiftiref', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuBool, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode], lltype.Void)),
    ('new_getvarpartiref', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuBool, MuTypeNode, MuVarNode], lltype.Void)),
    ('new_load', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuBool, MuFlag, MuTypeNode, MuVarNode, MuExcClause], lltype.Void)),
    ('new_store', rffi.CCallback([_MuIRBuilderPtr, MuID, MuBool, MuFlag, MuTypeNode, MuVarNode, MuVarNode, MuExcClause], lltype.Void)),
    ('new_cmpxchg', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuID, MuBool, MuBool, MuFlag, MuFlag, MuTypeNode, MuVarNode, MuVarNode, MuVarNode, MuExcClause], lltype.Void)),
    ('new_atomicrmw', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuBool, MuFlag, MuFlag, MuTypeNode, MuVarNode, MuVarNode, MuExcClause], lltype.Void)),
    ('new_fence', rffi.CCallback([_MuIRBuilderPtr, MuID, MuFlag], lltype.Void)),
    ('new_trap', rffi.CCallback([_MuIRBuilderPtr, MuID, MuIDPtr, MuTypeNodePtr, MuArraySize, MuExcClause, MuKeepaliveClause], lltype.Void)),
    ('new_watchpoint', rffi.CCallback([_MuIRBuilderPtr, MuID, MuWPID, MuIDPtr, MuTypeNodePtr, MuArraySize, MuDestClause, MuDestClause, MuDestClause, MuKeepaliveClause], lltype.Void)),
    ('new_wpbranch', rffi.CCallback([_MuIRBuilderPtr, MuID, MuWPID, MuDestClause, MuDestClause], lltype.Void)),
    ('new_ccall', rffi.CCallback([_MuIRBuilderPtr, MuID, MuIDPtr, MuArraySize, MuFlag, MuTypeNode, MuFuncSigNode, MuVarNode, MuVarNodePtr, MuArraySize, MuExcClause, MuKeepaliveClause], lltype.Void)),
    ('new_newthread', rffi.CCallback([_MuIRBuilderPtr, MuID, MuID, MuVarNode, MuVarNode, MuNewStackClause, MuExcClause], lltype.Void)),
    ('new_swapstack', rffi.CCallback([_MuIRBuilderPtr, MuID, MuIDPtr, MuArraySize, MuVarNode, MuCurStackClause, MuNewStackClause, MuExcClause, MuKeepaliveClause], lltype.Void)),
    ('new_comminst', rffi.CCallback([_MuIRBuilderPtr, MuID, MuIDPtr, MuArraySize, MuFlag, MuFlagPtr, MuArraySize, MuTypeNodePtr, MuArraySize, MuFuncSigNodePtr, MuArraySize, MuVarNodePtr, MuArraySize, MuExcClause, MuKeepaliveClause], lltype.Void)),
))

# -------------------------------------------------------------------------------------------------------
# Mu fast implementation functions
mu_new = rffi.llexternal('mu_fastimpl_new', [], _MuVMPtr, compilation_info=eci)
mu_fastimpl_new_with_opts = rffi.llexternal('mu_fastimpl_new_with_opts', [rffi.CCHARP], _MuVMPtr, compilation_info=eci)

# -------------------------------------------------------------------------------------------------------
# Helpers
def null(rmu_t):
    return lltype.nullptr(rmu_t.TO)

@specialize.ll()
def lst2arr(ELM_T, lst):
    sz = rffi.cast(MuArraySize, len(lst))

    if len(lst) == 0:
        buf = lltype.nullptr(rffi.CArray(ELM_T))
    else:
        if ELM_T == MuCString:
            buf = rffi.liststr2charpp(lst)
        else:
            buf = lltype.malloc(rffi.CArray(ELM_T), len(lst), flavor='raw')
            for i, e in enumerate(lst):
                buf[i] = rffi.cast(ELM_T, e)

    return buf, sz

