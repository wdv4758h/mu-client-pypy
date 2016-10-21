"""
Mu API RPython binding with C backend.
This file is auto-generated and then added a few minor modifications.
NOTE: THIS FILE IS *NOT* RPYTHON.
"""

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype

class CCall(object):
    __slots__ = ('fnc_name', 'args', 'rtn_var', 'context', 'check_err')

    def __init__(self, fnc_name, args, rtn_var, context=None, check_err=True):
        self.fnc_name = fnc_name
        self.args = args
        self.rtn_var = rtn_var
        self.context = context
        self.check_err = check_err

    def __str__(self):
        s = '{rtn_stm}{ctx}{fnc}({arg_lst})'.format(rtn_stm='%s = ' % self.rtn_var if self.rtn_var else '',
                                                    fnc=self.fnc_name,
                                                    arg_lst=', '.join(map(str, self.args)),
                                                    ctx='%s->' % self.context if self.context else '')
        if self.check_err:
            s = "CHECK(%s)" % s
        else:
            s = s + ";"
        return s

    __repr__ = __str__

class CStr(object):
    __slots__ = ('string', )

    def __init__(self, string):
        self.string = string

    def __str__(self):
        return '"%s"' % self.string

    def __len__(self):
        return len(self.string) - self.string.count('\\n')

    __repr__ = __str__

NULL = 'NULL'

class CArrayConst(object):
    def __init__(self, c_elm_t, lst):
        self.c_elm_t = c_elm_t
        self.lst = lst

    def __str__(self):
        return '({type}){value}'.format(type='%s [%d]' % (self.c_elm_t, len(self.lst)),
                                        value='{%s}' % ', '.join(map(str, self.lst)))

    __repr__ = __str__

class CVar(object):
    __slots__ = ('type', 'name')
    _name_dic = {}

    @staticmethod
    def new_name(base='var'):
        nd = CVar._name_dic
        if base in nd:
            count = nd[base]
            nd[base] += 1
            return '%(base)s_%(count)d' % locals()
        else:
            count = 2
            nd[base] = count
            return base

    def __init__(self, c_type, var_name=None):
        self.type = c_type
        if var_name:
            self.name = CVar.new_name(var_name)
        else:
            self.name = CVar.new_name()

    def __str__(self):
        return self.name

    __repr__ = __str__
class APILogger:
    def __init__(self):
        self.ccalls = []
        self.decl_vars = []

    def logcall(self, fnc_name, args, rtn_var, context=None):
        self.ccalls.append(CCall(fnc_name, args, rtn_var, context, False))
        if rtn_var:
            self.decl_vars.append(rtn_var)
    def genc(self, fp, exitcode=0):
        fp.write('\n'
                 '// Compile with flag -std=c99\n'
                 '#include <stdio.h>\n'
                 '#include <stdlib.h>\n'
                 '#include <stdbool.h>\n'
                 '#include "muapi.h"\n'
                 '#include "mu-fastimpl.h"\n')

        fp.write('int main(int argc, char** argv) {\n')
        idt = ' ' * 4
        for var in self.decl_vars:
            fp.write(idt + '%s %s;\n' % (var.type, var.name))

        for ccall in self.ccalls:
            fp.write(idt + '%(ccall)s\n' % locals())
        fp.write(idt + 'return %(exitcode)s;\n' % locals())
        fp.write('}\n')
_apilog = APILogger()
def get_global_apilogger():
    return _apilog

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
    THREAD_EXIT = "MU_THREAD_EXIT"
    REBIND_PASS_VALUES = "MU_REBIND_PASS_VALUES"
    REBIND_THROW_EXC = "MU_REBIND_THROW_EXC"
class MuBinOpStatus:
    N = "MU_BOS_N"
    Z = "MU_BOS_Z"
    C = "MU_BOS_C"
    V = "MU_BOS_V"
class MuBinOptr:
    ADD = "MU_BINOP_ADD"
    SUB = "MU_BINOP_SUB"
    MUL = "MU_BINOP_MUL"
    SDIV = "MU_BINOP_SDIV"
    SREM = "MU_BINOP_SREM"
    UDIV = "MU_BINOP_UDIV"
    UREM = "MU_BINOP_UREM"
    SHL = "MU_BINOP_SHL"
    LSHR = "MU_BINOP_LSHR"
    ASHR = "MU_BINOP_ASHR"
    AND = "MU_BINOP_AND"
    OR = "MU_BINOP_OR"
    XOR = "MU_BINOP_XOR"
    FADD = "MU_BINOP_FADD"
    FSUB = "MU_BINOP_FSUB"
    FMUL = "MU_BINOP_FMUL"
    FDIV = "MU_BINOP_FDIV"
    FREM = "MU_BINOP_FREM"
class MuCmpOptr:
    EQ = "MU_CMP_EQ"
    NE = "MU_CMP_NE"
    SGE = "MU_CMP_SGE"
    SGT = "MU_CMP_SGT"
    SLE = "MU_CMP_SLE"
    SLT = "MU_CMP_SLT"
    UGE = "MU_CMP_UGE"
    UGT = "MU_CMP_UGT"
    ULE = "MU_CMP_ULE"
    ULT = "MU_CMP_ULT"
    FFALSE = "MU_CMP_FFALSE"
    FTRUE = "MU_CMP_FTRUE"
    FUNO = "MU_CMP_FUNO"
    FUEQ = "MU_CMP_FUEQ"
    FUNE = "MU_CMP_FUNE"
    FUGT = "MU_CMP_FUGT"
    FUGE = "MU_CMP_FUGE"
    FULT = "MU_CMP_FULT"
    FULE = "MU_CMP_FULE"
    FORD = "MU_CMP_FORD"
    FOEQ = "MU_CMP_FOEQ"
    FONE = "MU_CMP_FONE"
    FOGT = "MU_CMP_FOGT"
    FOGE = "MU_CMP_FOGE"
    FOLT = "MU_CMP_FOLT"
    FOLE = "MU_CMP_FOLE"
class MuConvOptr:
    TRUNC = "MU_CONV_TRUNC"
    ZEXT = "MU_CONV_ZEXT"
    SEXT = "MU_CONV_SEXT"
    FPTRUNC = "MU_CONV_FPTRUNC"
    FPEXT = "MU_CONV_FPEXT"
    FPTOUI = "MU_CONV_FPTOUI"
    FPTOSI = "MU_CONV_FPTOSI"
    UITOFP = "MU_CONV_UITOFP"
    SITOFP = "MU_CONV_SITOFP"
    BITCAST = "MU_CONV_BITCAST"
    REFCAST = "MU_CONV_REFCAST"
    PTRCAST = "MU_CONV_PTRCAST"
class MuMemOrd:
    NOT_ATOMIC = "MU_ORD_NOT_ATOMIC"
    RELAXED = "MU_ORD_RELAXED"
    CONSUME = "MU_ORD_CONSUME"
    ACQUIRE = "MU_ORD_ACQUIRE"
    RELEASE = "MU_ORD_RELEASE"
    ACQ_REL = "MU_ORD_ACQ_REL"
    SEQ_CST = "MU_ORD_SEQ_CST"
class MuAtomicRMWOptr:
    XCHG = "MU_ARMW_XCHG"
    ADD = "MU_ARMW_ADD"
    SUB = "MU_ARMW_SUB"
    AND = "MU_ARMW_AND"
    NAND = "MU_ARMW_NAND"
    OR = "MU_ARMW_OR"
    XOR = "MU_ARMW_XOR"
    MAX = "MU_ARMW_MAX"
    MIN = "MU_ARMW_MIN"
    UMAX = "MU_ARMW_UMAX"
    UMIN = "MU_ARMW_UMIN"
class MuCallConv:
    DEFAULT = "MU_CC_DEFAULT"
class MuCommInst:
    NEW_STACK = "MU_CI_UVM_NEW_STACK"
    KILL_STACK = "MU_CI_UVM_KILL_STACK"
    THREAD_EXIT = "MU_CI_UVM_THREAD_EXIT"
    CURRENT_STACK = "MU_CI_UVM_CURRENT_STACK"
    SET_THREADLOCAL = "MU_CI_UVM_SET_THREADLOCAL"
    GET_THREADLOCAL = "MU_CI_UVM_GET_THREADLOCAL"
    TR64_IS_FP = "MU_CI_UVM_TR64_IS_FP"
    TR64_IS_INT = "MU_CI_UVM_TR64_IS_INT"
    TR64_IS_REF = "MU_CI_UVM_TR64_IS_REF"
    TR64_FROM_FP = "MU_CI_UVM_TR64_FROM_FP"
    TR64_FROM_INT = "MU_CI_UVM_TR64_FROM_INT"
    TR64_FROM_REF = "MU_CI_UVM_TR64_FROM_REF"
    TR64_TO_FP = "MU_CI_UVM_TR64_TO_FP"
    TR64_TO_INT = "MU_CI_UVM_TR64_TO_INT"
    TR64_TO_REF = "MU_CI_UVM_TR64_TO_REF"
    TR64_TO_TAG = "MU_CI_UVM_TR64_TO_TAG"
    FUTEX_WAIT = "MU_CI_UVM_FUTEX_WAIT"
    FUTEX_WAIT_TIMEOUT = "MU_CI_UVM_FUTEX_WAIT_TIMEOUT"
    FUTEX_WAKE = "MU_CI_UVM_FUTEX_WAKE"
    FUTEX_CMP_REQUEUE = "MU_CI_UVM_FUTEX_CMP_REQUEUE"
    KILL_DEPENDENCY = "MU_CI_UVM_KILL_DEPENDENCY"
    NATIVE_PIN = "MU_CI_UVM_NATIVE_PIN"
    NATIVE_UNPIN = "MU_CI_UVM_NATIVE_UNPIN"
    NATIVE_GET_ADDR = "MU_CI_UVM_NATIVE_GET_ADDR"
    NATIVE_EXPOSE = "MU_CI_UVM_NATIVE_EXPOSE"
    NATIVE_UNEXPOSE = "MU_CI_UVM_NATIVE_UNEXPOSE"
    NATIVE_GET_COOKIE = "MU_CI_UVM_NATIVE_GET_COOKIE"
    META_ID_OF = "MU_CI_UVM_META_ID_OF"
    META_NAME_OF = "MU_CI_UVM_META_NAME_OF"
    META_LOAD_BUNDLE = "MU_CI_UVM_META_LOAD_BUNDLE"
    META_LOAD_HAIL = "MU_CI_UVM_META_LOAD_HAIL"
    META_NEW_CURSOR = "MU_CI_UVM_META_NEW_CURSOR"
    META_NEXT_FRAME = "MU_CI_UVM_META_NEXT_FRAME"
    META_COPY_CURSOR = "MU_CI_UVM_META_COPY_CURSOR"
    META_CLOSE_CURSOR = "MU_CI_UVM_META_CLOSE_CURSOR"
    META_CUR_FUNC = "MU_CI_UVM_META_CUR_FUNC"
    META_CUR_FUNC_VER = "MU_CI_UVM_META_CUR_FUNC_VER"
    META_CUR_INST = "MU_CI_UVM_META_CUR_INST"
    META_DUMP_KEEPALIVES = "MU_CI_UVM_META_DUMP_KEEPALIVES"
    META_POP_FRAMES_TO = "MU_CI_UVM_META_POP_FRAMES_TO"
    META_PUSH_FRAME = "MU_CI_UVM_META_PUSH_FRAME"
    META_ENABLE_WATCHPOINT = "MU_CI_UVM_META_ENABLE_WATCHPOINT"
    META_DISABLE_WATCHPOINT = "MU_CI_UVM_META_DISABLE_WATCHPOINT"
    META_SET_TRAP_HANDLER = "MU_CI_UVM_META_SET_TRAP_HANDLER"
    IRBUILDER_NEW_IR_BUILDER = "MU_CI_UVM_IRBUILDER_NEW_IR_BUILDER"
    IRBUILDER_LOAD = "MU_CI_UVM_IRBUILDER_LOAD"
    IRBUILDER_ABORT = "MU_CI_UVM_IRBUILDER_ABORT"
    IRBUILDER_GEN_SYM = "MU_CI_UVM_IRBUILDER_GEN_SYM"
    IRBUILDER_NEW_TYPE_INT = "MU_CI_UVM_IRBUILDER_NEW_TYPE_INT"
    IRBUILDER_NEW_TYPE_FLOAT = "MU_CI_UVM_IRBUILDER_NEW_TYPE_FLOAT"
    IRBUILDER_NEW_TYPE_DOUBLE = "MU_CI_UVM_IRBUILDER_NEW_TYPE_DOUBLE"
    IRBUILDER_NEW_TYPE_UPTR = "MU_CI_UVM_IRBUILDER_NEW_TYPE_UPTR"
    IRBUILDER_NEW_TYPE_UFUNCPTR = "MU_CI_UVM_IRBUILDER_NEW_TYPE_UFUNCPTR"
    IRBUILDER_NEW_TYPE_STRUCT = "MU_CI_UVM_IRBUILDER_NEW_TYPE_STRUCT"
    IRBUILDER_NEW_TYPE_HYBRID = "MU_CI_UVM_IRBUILDER_NEW_TYPE_HYBRID"
    IRBUILDER_NEW_TYPE_ARRAY = "MU_CI_UVM_IRBUILDER_NEW_TYPE_ARRAY"
    IRBUILDER_NEW_TYPE_VECTOR = "MU_CI_UVM_IRBUILDER_NEW_TYPE_VECTOR"
    IRBUILDER_NEW_TYPE_VOID = "MU_CI_UVM_IRBUILDER_NEW_TYPE_VOID"
    IRBUILDER_NEW_TYPE_REF = "MU_CI_UVM_IRBUILDER_NEW_TYPE_REF"
    IRBUILDER_NEW_TYPE_IREF = "MU_CI_UVM_IRBUILDER_NEW_TYPE_IREF"
    IRBUILDER_NEW_TYPE_WEAKREF = "MU_CI_UVM_IRBUILDER_NEW_TYPE_WEAKREF"
    IRBUILDER_NEW_TYPE_FUNCREF = "MU_CI_UVM_IRBUILDER_NEW_TYPE_FUNCREF"
    IRBUILDER_NEW_TYPE_TAGREF64 = "MU_CI_UVM_IRBUILDER_NEW_TYPE_TAGREF64"
    IRBUILDER_NEW_TYPE_THREADREF = "MU_CI_UVM_IRBUILDER_NEW_TYPE_THREADREF"
    IRBUILDER_NEW_TYPE_STACKREF = "MU_CI_UVM_IRBUILDER_NEW_TYPE_STACKREF"
    IRBUILDER_NEW_TYPE_FRAMECURSORREF = "MU_CI_UVM_IRBUILDER_NEW_TYPE_FRAMECURSORREF"
    IRBUILDER_NEW_TYPE_IRBUILDERREF = "MU_CI_UVM_IRBUILDER_NEW_TYPE_IRBUILDERREF"
    IRBUILDER_NEW_FUNCSIG = "MU_CI_UVM_IRBUILDER_NEW_FUNCSIG"
    IRBUILDER_NEW_CONST_INT = "MU_CI_UVM_IRBUILDER_NEW_CONST_INT"
    IRBUILDER_NEW_CONST_INT_EX = "MU_CI_UVM_IRBUILDER_NEW_CONST_INT_EX"
    IRBUILDER_NEW_CONST_FLOAT = "MU_CI_UVM_IRBUILDER_NEW_CONST_FLOAT"
    IRBUILDER_NEW_CONST_DOUBLE = "MU_CI_UVM_IRBUILDER_NEW_CONST_DOUBLE"
    IRBUILDER_NEW_CONST_NULL = "MU_CI_UVM_IRBUILDER_NEW_CONST_NULL"
    IRBUILDER_NEW_CONST_SEQ = "MU_CI_UVM_IRBUILDER_NEW_CONST_SEQ"
    IRBUILDER_NEW_CONST_EXTERN = "MU_CI_UVM_IRBUILDER_NEW_CONST_EXTERN"
    IRBUILDER_NEW_GLOBAL_CELL = "MU_CI_UVM_IRBUILDER_NEW_GLOBAL_CELL"
    IRBUILDER_NEW_FUNC = "MU_CI_UVM_IRBUILDER_NEW_FUNC"
    IRBUILDER_NEW_EXP_FUNC = "MU_CI_UVM_IRBUILDER_NEW_EXP_FUNC"
    IRBUILDER_NEW_FUNC_VER = "MU_CI_UVM_IRBUILDER_NEW_FUNC_VER"
    IRBUILDER_NEW_BB = "MU_CI_UVM_IRBUILDER_NEW_BB"
    IRBUILDER_NEW_DEST_CLAUSE = "MU_CI_UVM_IRBUILDER_NEW_DEST_CLAUSE"
    IRBUILDER_NEW_EXC_CLAUSE = "MU_CI_UVM_IRBUILDER_NEW_EXC_CLAUSE"
    IRBUILDER_NEW_KEEPALIVE_CLAUSE = "MU_CI_UVM_IRBUILDER_NEW_KEEPALIVE_CLAUSE"
    IRBUILDER_NEW_CSC_RET_WITH = "MU_CI_UVM_IRBUILDER_NEW_CSC_RET_WITH"
    IRBUILDER_NEW_CSC_KILL_OLD = "MU_CI_UVM_IRBUILDER_NEW_CSC_KILL_OLD"
    IRBUILDER_NEW_NSC_PASS_VALUES = "MU_CI_UVM_IRBUILDER_NEW_NSC_PASS_VALUES"
    IRBUILDER_NEW_NSC_THROW_EXC = "MU_CI_UVM_IRBUILDER_NEW_NSC_THROW_EXC"
    IRBUILDER_NEW_BINOP = "MU_CI_UVM_IRBUILDER_NEW_BINOP"
    IRBUILDER_NEW_BINOP_WITH_STATUS = "MU_CI_UVM_IRBUILDER_NEW_BINOP_WITH_STATUS"
    IRBUILDER_NEW_CMP = "MU_CI_UVM_IRBUILDER_NEW_CMP"
    IRBUILDER_NEW_CONV = "MU_CI_UVM_IRBUILDER_NEW_CONV"
    IRBUILDER_NEW_SELECT = "MU_CI_UVM_IRBUILDER_NEW_SELECT"
    IRBUILDER_NEW_BRANCH = "MU_CI_UVM_IRBUILDER_NEW_BRANCH"
    IRBUILDER_NEW_BRANCH2 = "MU_CI_UVM_IRBUILDER_NEW_BRANCH2"
    IRBUILDER_NEW_SWITCH = "MU_CI_UVM_IRBUILDER_NEW_SWITCH"
    IRBUILDER_NEW_CALL = "MU_CI_UVM_IRBUILDER_NEW_CALL"
    IRBUILDER_NEW_TAILCALL = "MU_CI_UVM_IRBUILDER_NEW_TAILCALL"
    IRBUILDER_NEW_RET = "MU_CI_UVM_IRBUILDER_NEW_RET"
    IRBUILDER_NEW_THROW = "MU_CI_UVM_IRBUILDER_NEW_THROW"
    IRBUILDER_NEW_EXTRACTVALUE = "MU_CI_UVM_IRBUILDER_NEW_EXTRACTVALUE"
    IRBUILDER_NEW_INSERTVALUE = "MU_CI_UVM_IRBUILDER_NEW_INSERTVALUE"
    IRBUILDER_NEW_EXTRACTELEMENT = "MU_CI_UVM_IRBUILDER_NEW_EXTRACTELEMENT"
    IRBUILDER_NEW_INSERTELEMENT = "MU_CI_UVM_IRBUILDER_NEW_INSERTELEMENT"
    IRBUILDER_NEW_SHUFFLEVECTOR = "MU_CI_UVM_IRBUILDER_NEW_SHUFFLEVECTOR"
    IRBUILDER_NEW_NEW = "MU_CI_UVM_IRBUILDER_NEW_NEW"
    IRBUILDER_NEW_NEWHYBRID = "MU_CI_UVM_IRBUILDER_NEW_NEWHYBRID"
    IRBUILDER_NEW_ALLOCA = "MU_CI_UVM_IRBUILDER_NEW_ALLOCA"
    IRBUILDER_NEW_ALLOCAHYBRID = "MU_CI_UVM_IRBUILDER_NEW_ALLOCAHYBRID"
    IRBUILDER_NEW_GETIREF = "MU_CI_UVM_IRBUILDER_NEW_GETIREF"
    IRBUILDER_NEW_GETFIELDIREF = "MU_CI_UVM_IRBUILDER_NEW_GETFIELDIREF"
    IRBUILDER_NEW_GETELEMIREF = "MU_CI_UVM_IRBUILDER_NEW_GETELEMIREF"
    IRBUILDER_NEW_SHIFTIREF = "MU_CI_UVM_IRBUILDER_NEW_SHIFTIREF"
    IRBUILDER_NEW_GETVARPARTIREF = "MU_CI_UVM_IRBUILDER_NEW_GETVARPARTIREF"
    IRBUILDER_NEW_LOAD = "MU_CI_UVM_IRBUILDER_NEW_LOAD"
    IRBUILDER_NEW_STORE = "MU_CI_UVM_IRBUILDER_NEW_STORE"
    IRBUILDER_NEW_CMPXCHG = "MU_CI_UVM_IRBUILDER_NEW_CMPXCHG"
    IRBUILDER_NEW_ATOMICRMW = "MU_CI_UVM_IRBUILDER_NEW_ATOMICRMW"
    IRBUILDER_NEW_FENCE = "MU_CI_UVM_IRBUILDER_NEW_FENCE"
    IRBUILDER_NEW_TRAP = "MU_CI_UVM_IRBUILDER_NEW_TRAP"
    IRBUILDER_NEW_WATCHPOINT = "MU_CI_UVM_IRBUILDER_NEW_WATCHPOINT"
    IRBUILDER_NEW_WPBRANCH = "MU_CI_UVM_IRBUILDER_NEW_WPBRANCH"
    IRBUILDER_NEW_CCALL = "MU_CI_UVM_IRBUILDER_NEW_CCALL"
    IRBUILDER_NEW_NEWTHREAD = "MU_CI_UVM_IRBUILDER_NEW_NEWTHREAD"
    IRBUILDER_NEW_SWAPSTACK = "MU_CI_UVM_IRBUILDER_NEW_SWAPSTACK"
    IRBUILDER_NEW_COMMINST = "MU_CI_UVM_IRBUILDER_NEW_COMMINST"

MU_NO_ID = "MU_NO_ID"

# -------------------------------------------------------------------------------------------------------
# OO wrappers
class MuVM:
    def __init__(self):
        self._mu = CVar('MuVM*', 'mu')
        _apilog.logcall('mu_fastimpl_new', [], self._mu)

    def new_context(self):
        # type: () -> MuCtx
        res_var = CVar('MuCtx*', 'ctx')
        _apilog.logcall('new_context', [self._mu], res_var, self._mu)
        return MuCtx(res_var)

    def id_of(self, name):
        # type: (str) -> MuID
        name_cstr = CStr(name) if name else NULL
        res_var = CVar('MuID', 'id')
        _apilog.logcall('id_of', [self._mu, name_cstr], res_var, self._mu)
        return res_var

    def name_of(self, id):
        # type: (MuID) -> str
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('MuName', 'var')
        _apilog.logcall('name_of', [self._mu, id], res_var, self._mu)
        return res_var

    def set_trap_handler(self, trap_handler, userdata):
        # type: (MuTrapHandler, MuCPtr) -> None
        _apilog.logcall('set_trap_handler', [self._mu, trap_handler, userdata], None, self._mu)

    def compile_to_sharedlib(self, fncname):
        # type: (str) -> str
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        fncname_cstr = CStr(fncname) if fncname else NULL
        res_var = CVar('MuCString', 'var')
        _apilog.logcall('compile_to_sharedlib', [self._mu, fncname_cstr], res_var, self._mu)
        return res_var


class MuCtx:
    def __init__(self, ctx_var):
        self._ctx = ctx_var
    def id_of(self, name):
        # type: (str) -> MuID
        name_cstr = CStr(name) if name else NULL
        res_var = CVar('MuID', 'id')
        _apilog.logcall('id_of', [self._ctx, name_cstr], res_var, self._ctx)
        return res_var

    def name_of(self, id):
        # type: (MuID) -> str
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('MuName', 'var')
        _apilog.logcall('name_of', [self._ctx, id], res_var, self._ctx)
        return res_var

    def close_context(self):
        # type: () -> None
        _apilog.logcall('close_context', [self._ctx], None, self._ctx)

    def load_bundle(self, buf):
        # type: (str) -> None
        buf_cstr = CStr(buf) if buf else NULL
        sz = len(buf_cstr)
        _apilog.logcall('load_bundle', [self._ctx, buf_cstr, sz], None, self._ctx)

    def load_hail(self, buf):
        # type: (str) -> None
        buf_cstr = CStr(buf) if buf else NULL
        sz = len(buf_cstr)
        _apilog.logcall('load_hail', [self._ctx, buf_cstr, sz], None, self._ctx)

    def handle_from_sint8(self, num, len):
        # type: (int, int) -> MuIntValue
        res_var = CVar('MuIntValue', 'hintval')
        _apilog.logcall('handle_from_sint8', [self._ctx, num, len], res_var, self._ctx)
        return res_var

    def handle_from_uint8(self, num, len):
        # type: (int, int) -> MuIntValue
        res_var = CVar('MuIntValue', 'hintval')
        _apilog.logcall('handle_from_uint8', [self._ctx, num, len], res_var, self._ctx)
        return res_var

    def handle_from_sint16(self, num, len):
        # type: (int, int) -> MuIntValue
        res_var = CVar('MuIntValue', 'hintval')
        _apilog.logcall('handle_from_sint16', [self._ctx, num, len], res_var, self._ctx)
        return res_var

    def handle_from_uint16(self, num, len):
        # type: (int, int) -> MuIntValue
        res_var = CVar('MuIntValue', 'hintval')
        _apilog.logcall('handle_from_uint16', [self._ctx, num, len], res_var, self._ctx)
        return res_var

    def handle_from_sint32(self, num, len):
        # type: (int, int) -> MuIntValue
        res_var = CVar('MuIntValue', 'hintval')
        _apilog.logcall('handle_from_sint32', [self._ctx, num, len], res_var, self._ctx)
        return res_var

    def handle_from_uint32(self, num, len):
        # type: (int, int) -> MuIntValue
        res_var = CVar('MuIntValue', 'hintval')
        _apilog.logcall('handle_from_uint32', [self._ctx, num, len], res_var, self._ctx)
        return res_var

    def handle_from_sint64(self, num, len):
        # type: (int, int) -> MuIntValue
        res_var = CVar('MuIntValue', 'hintval')
        _apilog.logcall('handle_from_sint64', [self._ctx, num, len], res_var, self._ctx)
        return res_var

    def handle_from_uint64(self, num, len):
        # type: (int, int) -> MuIntValue
        res_var = CVar('MuIntValue', 'hintval')
        _apilog.logcall('handle_from_uint64', [self._ctx, num, len], res_var, self._ctx)
        return res_var

    def handle_from_uint64s(self, nums, len):
        # type: ([rffi.ULONG], int) -> MuIntValue
        nums_arr, nums_sz = lst2arr('uint64_t', nums)
        res_var = CVar('MuIntValue', 'hintval')
        _apilog.logcall('handle_from_uint64s', [self._ctx, nums_arr, nums_sz, len], res_var, self._ctx)
        return res_var

    def handle_from_float(self, num):
        # type: (float) -> MuFloatValue
        num_fltstr = '%.20f' % num
        res_var = CVar('MuFloatValue', 'hfltval')
        _apilog.logcall('handle_from_float', [self._ctx, num_fltstr], res_var, self._ctx)
        return res_var

    def handle_from_double(self, num):
        # type: (float) -> MuDoubleValue
        num_fltstr = '%.20f' % num
        res_var = CVar('MuDoubleValue', 'hdblval')
        _apilog.logcall('handle_from_double', [self._ctx, num_fltstr], res_var, self._ctx)
        return res_var

    def handle_from_ptr(self, mu_type, ptr):
        # type: (MuID, MuCPtr) -> MuUPtrValue
        res_var = CVar('MuUPtrValue', 'huptrval')
        _apilog.logcall('handle_from_ptr', [self._ctx, mu_type, ptr], res_var, self._ctx)
        return res_var

    def handle_from_fp(self, mu_type, fp):
        # type: (MuID, MuCFP) -> MuUFPValue
        res_var = CVar('MuUFPValue', 'hufpval')
        _apilog.logcall('handle_from_fp', [self._ctx, mu_type, fp], res_var, self._ctx)
        return res_var

    def handle_to_sint8(self, opnd):
        # type: (MuIntValue) -> int
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('int8_t', 'var')
        _apilog.logcall('handle_to_sint8', [self._ctx, opnd], res_var, self._ctx)
        return res_var

    def handle_to_uint8(self, opnd):
        # type: (MuIntValue) -> int
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('uint8_t', 'var')
        _apilog.logcall('handle_to_uint8', [self._ctx, opnd], res_var, self._ctx)
        return res_var

    def handle_to_sint16(self, opnd):
        # type: (MuIntValue) -> int
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('int16_t', 'var')
        _apilog.logcall('handle_to_sint16', [self._ctx, opnd], res_var, self._ctx)
        return res_var

    def handle_to_uint16(self, opnd):
        # type: (MuIntValue) -> int
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('uint16_t', 'var')
        _apilog.logcall('handle_to_uint16', [self._ctx, opnd], res_var, self._ctx)
        return res_var

    def handle_to_sint32(self, opnd):
        # type: (MuIntValue) -> int
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('int32_t', 'var')
        _apilog.logcall('handle_to_sint32', [self._ctx, opnd], res_var, self._ctx)
        return res_var

    def handle_to_uint32(self, opnd):
        # type: (MuIntValue) -> int
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('uint32_t', 'var')
        _apilog.logcall('handle_to_uint32', [self._ctx, opnd], res_var, self._ctx)
        return res_var

    def handle_to_sint64(self, opnd):
        # type: (MuIntValue) -> int
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('int64_t', 'var')
        _apilog.logcall('handle_to_sint64', [self._ctx, opnd], res_var, self._ctx)
        return res_var

    def handle_to_uint64(self, opnd):
        # type: (MuIntValue) -> int
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('uint64_t', 'var')
        _apilog.logcall('handle_to_uint64', [self._ctx, opnd], res_var, self._ctx)
        return res_var

    def handle_to_float(self, opnd):
        # type: (MuFloatValue) -> float
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('float', 'var')
        _apilog.logcall('handle_to_float', [self._ctx, opnd], res_var, self._ctx)
        return res_var

    def handle_to_double(self, opnd):
        # type: (MuDoubleValue) -> float
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('double', 'var')
        _apilog.logcall('handle_to_double', [self._ctx, opnd], res_var, self._ctx)
        return res_var

    def handle_to_ptr(self, opnd):
        # type: (MuUPtrValue) -> MuCPtr
        res_var = CVar('MuCPtr', 'var')
        _apilog.logcall('handle_to_ptr', [self._ctx, opnd], res_var, self._ctx)
        return res_var

    def handle_to_fp(self, opnd):
        # type: (MuUFPValue) -> MuCFP
        res_var = CVar('MuCFP', 'var')
        _apilog.logcall('handle_to_fp', [self._ctx, opnd], res_var, self._ctx)
        return res_var

    def handle_from_const(self, id):
        # type: (MuID) -> MuValue
        res_var = CVar('MuValue', 'hdl')
        _apilog.logcall('handle_from_const', [self._ctx, id], res_var, self._ctx)
        return res_var

    def handle_from_global(self, id):
        # type: (MuID) -> MuIRefValue
        res_var = CVar('MuIRefValue', 'hiref')
        _apilog.logcall('handle_from_global', [self._ctx, id], res_var, self._ctx)
        return res_var

    def handle_from_func(self, id):
        # type: (MuID) -> MuFuncRefValue
        res_var = CVar('MuFuncRefValue', 'hfncref')
        _apilog.logcall('handle_from_func', [self._ctx, id], res_var, self._ctx)
        return res_var

    def handle_from_expose(self, id):
        # type: (MuID) -> MuValue
        res_var = CVar('MuValue', 'hdl')
        _apilog.logcall('handle_from_expose', [self._ctx, id], res_var, self._ctx)
        return res_var

    def delete_value(self, opnd):
        # type: (MuValue) -> None
        _apilog.logcall('delete_value', [self._ctx, opnd], None, self._ctx)

    def ref_eq(self, lhs, rhs):
        # type: (MuGenRefValue, MuGenRefValue) -> bool
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('MuBool', 'var')
        _apilog.logcall('ref_eq', [self._ctx, lhs, rhs], res_var, self._ctx)
        return res_var

    def ref_ult(self, lhs, rhs):
        # type: (MuIRefValue, MuIRefValue) -> bool
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('MuBool', 'var')
        _apilog.logcall('ref_ult', [self._ctx, lhs, rhs], res_var, self._ctx)
        return res_var

    def extract_value(self, str, index):
        # type: (MuStructValue, int) -> MuValue
        res_var = CVar('MuValue', 'hdl')
        _apilog.logcall('extract_value', [self._ctx, str, index], res_var, self._ctx)
        return res_var

    def insert_value(self, str, index, newval):
        # type: (MuStructValue, int, MuValue) -> MuStructValue
        res_var = CVar('MuStructValue', 'hstt')
        _apilog.logcall('insert_value', [self._ctx, str, index, newval], res_var, self._ctx)
        return res_var

    def extract_element(self, str, index):
        # type: (MuSeqValue, MuIntValue) -> MuValue
        res_var = CVar('MuValue', 'hdl')
        _apilog.logcall('extract_element', [self._ctx, str, index], res_var, self._ctx)
        return res_var

    def insert_element(self, str, index, newval):
        # type: (MuSeqValue, MuIntValue, MuValue) -> MuSeqValue
        res_var = CVar('MuSeqValue', 'hseq')
        _apilog.logcall('insert_element', [self._ctx, str, index, newval], res_var, self._ctx)
        return res_var

    def new_fixed(self, mu_type):
        # type: (MuID) -> MuRefValue
        res_var = CVar('MuRefValue', 'href')
        _apilog.logcall('new_fixed', [self._ctx, mu_type], res_var, self._ctx)
        return res_var

    def new_hybrid(self, mu_type, length):
        # type: (MuID, MuIntValue) -> MuRefValue
        res_var = CVar('MuRefValue', 'href')
        _apilog.logcall('new_hybrid', [self._ctx, mu_type, length], res_var, self._ctx)
        return res_var

    def refcast(self, opnd, new_type):
        # type: (MuGenRefValue, MuID) -> MuGenRefValue
        res_var = CVar('MuGenRefValue', 'var')
        _apilog.logcall('refcast', [self._ctx, opnd, new_type], res_var, self._ctx)
        return res_var

    def get_iref(self, opnd):
        # type: (MuRefValue) -> MuIRefValue
        res_var = CVar('MuIRefValue', 'hiref')
        _apilog.logcall('get_iref', [self._ctx, opnd], res_var, self._ctx)
        return res_var

    def get_field_iref(self, opnd, field):
        # type: (MuIRefValue, int) -> MuIRefValue
        res_var = CVar('MuIRefValue', 'hiref')
        _apilog.logcall('get_field_iref', [self._ctx, opnd, field], res_var, self._ctx)
        return res_var

    def get_elem_iref(self, opnd, index):
        # type: (MuIRefValue, MuIntValue) -> MuIRefValue
        res_var = CVar('MuIRefValue', 'hiref')
        _apilog.logcall('get_elem_iref', [self._ctx, opnd, index], res_var, self._ctx)
        return res_var

    def shift_iref(self, opnd, offset):
        # type: (MuIRefValue, MuIntValue) -> MuIRefValue
        res_var = CVar('MuIRefValue', 'hiref')
        _apilog.logcall('shift_iref', [self._ctx, opnd, offset], res_var, self._ctx)
        return res_var

    def get_var_part_iref(self, opnd):
        # type: (MuIRefValue) -> MuIRefValue
        res_var = CVar('MuIRefValue', 'hiref')
        _apilog.logcall('get_var_part_iref', [self._ctx, opnd], res_var, self._ctx)
        return res_var

    def load(self, ord, loc):
        # type: (MuFlag, MuIRefValue) -> MuValue
        res_var = CVar('MuValue', 'hdl')
        _apilog.logcall('load', [self._ctx, ord, loc], res_var, self._ctx)
        return res_var

    def store(self, ord, loc, newval):
        # type: (MuFlag, MuIRefValue, MuValue) -> None
        _apilog.logcall('store', [self._ctx, ord, loc, newval], None, self._ctx)

    def cmpxchg(self, ord_succ, ord_fail, weak, loc, expected, desired, is_succ):
        # type: (MuFlag, MuFlag, bool, MuIRefValue, MuValue, MuValue, MuBoolPtr) -> MuValue
        weak_bool = 'true' if weak else 'false'
        res_var = CVar('MuValue', 'hdl')
        _apilog.logcall('cmpxchg', [self._ctx, ord_succ, ord_fail, weak_bool, loc, expected, desired, is_succ], res_var, self._ctx)
        return res_var

    def atomicrmw(self, ord, op, loc, opnd):
        # type: (MuFlag, MuFlag, MuIRefValue, MuValue) -> MuValue
        res_var = CVar('MuValue', 'hdl')
        _apilog.logcall('atomicrmw', [self._ctx, ord, op, loc, opnd], res_var, self._ctx)
        return res_var

    def fence(self, ord):
        # type: (MuFlag) -> None
        _apilog.logcall('fence', [self._ctx, ord], None, self._ctx)

    def new_stack(self, func):
        # type: (MuFuncRefValue) -> MuStackRefValue
        res_var = CVar('MuStackRefValue', 'hstkref')
        _apilog.logcall('new_stack', [self._ctx, func], res_var, self._ctx)
        return res_var

    def new_thread_nor(self, stack, threadlocal, vals):
        # type: (MuStackRefValue, MuRefValue, [MuValue]) -> MuThreadRefValue
        vals_arr, vals_sz = lst2arr('MuValue', vals)
        res_var = CVar('MuThreadRefValue', 'hthdref')
        _apilog.logcall('new_thread_nor', [self._ctx, stack, threadlocal, vals_arr, vals_sz], res_var, self._ctx)
        return res_var

    def new_thread_exc(self, stack, threadlocal, exc):
        # type: (MuStackRefValue, MuRefValue, MuRefValue) -> MuThreadRefValue
        res_var = CVar('MuThreadRefValue', 'hthdref')
        _apilog.logcall('new_thread_exc', [self._ctx, stack, threadlocal, exc], res_var, self._ctx)
        return res_var

    def kill_stack(self, stack):
        # type: (MuStackRefValue) -> None
        _apilog.logcall('kill_stack', [self._ctx, stack], None, self._ctx)

    def set_threadlocal(self, thread, threadlocal):
        # type: (MuThreadRefValue, MuRefValue) -> None
        _apilog.logcall('set_threadlocal', [self._ctx, thread, threadlocal], None, self._ctx)

    def get_threadlocal(self, thread):
        # type: (MuThreadRefValue) -> MuRefValue
        res_var = CVar('MuRefValue', 'href')
        _apilog.logcall('get_threadlocal', [self._ctx, thread], res_var, self._ctx)
        return res_var

    def new_cursor(self, stack):
        # type: (MuStackRefValue) -> MuFCRefValue
        res_var = CVar('MuFCRefValue', 'hfcr')
        _apilog.logcall('new_cursor', [self._ctx, stack], res_var, self._ctx)
        return res_var

    def next_frame(self, cursor):
        # type: (MuFCRefValue) -> None
        _apilog.logcall('next_frame', [self._ctx, cursor], None, self._ctx)

    def copy_cursor(self, cursor):
        # type: (MuFCRefValue) -> MuFCRefValue
        res_var = CVar('MuFCRefValue', 'hfcr')
        _apilog.logcall('copy_cursor', [self._ctx, cursor], res_var, self._ctx)
        return res_var

    def close_cursor(self, cursor):
        # type: (MuFCRefValue) -> None
        _apilog.logcall('close_cursor', [self._ctx, cursor], None, self._ctx)

    def cur_func(self, cursor):
        # type: (MuFCRefValue) -> MuID
        res_var = CVar('MuID', 'id')
        _apilog.logcall('cur_func', [self._ctx, cursor], res_var, self._ctx)
        return res_var

    def cur_func_ver(self, cursor):
        # type: (MuFCRefValue) -> MuID
        res_var = CVar('MuID', 'id')
        _apilog.logcall('cur_func_ver', [self._ctx, cursor], res_var, self._ctx)
        return res_var

    def cur_inst(self, cursor):
        # type: (MuFCRefValue) -> MuID
        res_var = CVar('MuID', 'id')
        _apilog.logcall('cur_inst', [self._ctx, cursor], res_var, self._ctx)
        return res_var

    def dump_keepalives(self, cursor, results):
        # type: (MuFCRefValue, MuValuePtr) -> None
        _apilog.logcall('dump_keepalives', [self._ctx, cursor, results], None, self._ctx)

    def pop_frames_to(self, cursor):
        # type: (MuFCRefValue) -> None
        _apilog.logcall('pop_frames_to', [self._ctx, cursor], None, self._ctx)

    def push_frame(self, stack, func):
        # type: (MuStackRefValue, MuFuncRefValue) -> None
        _apilog.logcall('push_frame', [self._ctx, stack, func], None, self._ctx)

    def tr64_is_fp(self, value):
        # type: (MuTagRef64Value) -> bool
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('MuBool', 'var')
        _apilog.logcall('tr64_is_fp', [self._ctx, value], res_var, self._ctx)
        return res_var

    def tr64_is_int(self, value):
        # type: (MuTagRef64Value) -> bool
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('MuBool', 'var')
        _apilog.logcall('tr64_is_int', [self._ctx, value], res_var, self._ctx)
        return res_var

    def tr64_is_ref(self, value):
        # type: (MuTagRef64Value) -> bool
        # NOTE: runtime dependent method, the return value should not be examined in Python.
        res_var = CVar('MuBool', 'var')
        _apilog.logcall('tr64_is_ref', [self._ctx, value], res_var, self._ctx)
        return res_var

    def tr64_to_fp(self, value):
        # type: (MuTagRef64Value) -> MuDoubleValue
        res_var = CVar('MuDoubleValue', 'hdblval')
        _apilog.logcall('tr64_to_fp', [self._ctx, value], res_var, self._ctx)
        return res_var

    def tr64_to_int(self, value):
        # type: (MuTagRef64Value) -> MuIntValue
        res_var = CVar('MuIntValue', 'hintval')
        _apilog.logcall('tr64_to_int', [self._ctx, value], res_var, self._ctx)
        return res_var

    def tr64_to_ref(self, value):
        # type: (MuTagRef64Value) -> MuRefValue
        res_var = CVar('MuRefValue', 'href')
        _apilog.logcall('tr64_to_ref', [self._ctx, value], res_var, self._ctx)
        return res_var

    def tr64_to_tag(self, value):
        # type: (MuTagRef64Value) -> MuIntValue
        res_var = CVar('MuIntValue', 'hintval')
        _apilog.logcall('tr64_to_tag', [self._ctx, value], res_var, self._ctx)
        return res_var

    def tr64_from_fp(self, value):
        # type: (MuDoubleValue) -> MuTagRef64Value
        res_var = CVar('MuTagRef64Value', 'htag')
        _apilog.logcall('tr64_from_fp', [self._ctx, value], res_var, self._ctx)
        return res_var

    def tr64_from_int(self, value):
        # type: (MuIntValue) -> MuTagRef64Value
        res_var = CVar('MuTagRef64Value', 'htag')
        _apilog.logcall('tr64_from_int', [self._ctx, value], res_var, self._ctx)
        return res_var

    def tr64_from_ref(self, ref, tag):
        # type: (MuRefValue, MuIntValue) -> MuTagRef64Value
        res_var = CVar('MuTagRef64Value', 'htag')
        _apilog.logcall('tr64_from_ref', [self._ctx, ref, tag], res_var, self._ctx)
        return res_var

    def enable_watchpoint(self, wpid):
        # type: (MuWPID) -> None
        _apilog.logcall('enable_watchpoint', [self._ctx, wpid], None, self._ctx)

    def disable_watchpoint(self, wpid):
        # type: (MuWPID) -> None
        _apilog.logcall('disable_watchpoint', [self._ctx, wpid], None, self._ctx)

    def pin(self, loc):
        # type: (MuValue) -> MuUPtrValue
        res_var = CVar('MuUPtrValue', 'huptrval')
        _apilog.logcall('pin', [self._ctx, loc], res_var, self._ctx)
        return res_var

    def unpin(self, loc):
        # type: (MuValue) -> None
        _apilog.logcall('unpin', [self._ctx, loc], None, self._ctx)

    def get_addr(self, loc):
        # type: (MuValue) -> MuUPtrValue
        res_var = CVar('MuUPtrValue', 'huptrval')
        _apilog.logcall('get_addr', [self._ctx, loc], res_var, self._ctx)
        return res_var

    def expose(self, func, call_conv, cookie):
        # type: (MuFuncRefValue, MuFlag, MuIntValue) -> MuValue
        res_var = CVar('MuValue', 'hdl')
        _apilog.logcall('expose', [self._ctx, func, call_conv, cookie], res_var, self._ctx)
        return res_var

    def unexpose(self, call_conv, value):
        # type: (MuFlag, MuValue) -> None
        _apilog.logcall('unexpose', [self._ctx, call_conv, value], None, self._ctx)

    def new_ir_builder(self):
        # type: () -> MuIRBuilder
        res_var = CVar('MuIRBuilder*', 'bldr')
        _apilog.logcall('new_ir_builder', [self._ctx], res_var, self._ctx)
        return MuIRBuilder(res_var)

    def make_boot_image(self, whitelist, primordial_func, primordial_stack, primordial_threadlocal, sym_fields, sym_strings, reloc_fields, reloc_strings, output_file):
        # type: ([MuID], MuFuncRefValue, MuStackRefValue, MuRefValue, [MuIRefValue], [MuCString], [MuIRefValue], [MuCString], str) -> None
        whitelist_arr, whitelist_sz = lst2arr('MuID', whitelist)
        sym_fields_arr, sym_fields_sz = lst2arr('MuIRefValue', sym_fields)
        sym_strings_arr, sym_strings_sz = lst2arr('MuCString', sym_strings)
        reloc_fields_arr, reloc_fields_sz = lst2arr('MuIRefValue', reloc_fields)
        reloc_strings_arr, reloc_strings_sz = lst2arr('MuCString', reloc_strings)
        output_file_cstr = CStr(output_file) if output_file else NULL
        _apilog.logcall('make_boot_image', [self._ctx, whitelist_arr, whitelist_sz, primordial_func, primordial_stack, primordial_threadlocal, sym_fields_arr, sym_strings_arr, sym_strings_sz, reloc_fields_arr, reloc_strings_arr, reloc_strings_sz, output_file_cstr], None, self._ctx)


class MuIRBuilder:
    def __init__(self, bldr_var):
        self._bldr = bldr_var

    def load(self):
        # type: () -> None
        _apilog.logcall('load', [self._bldr], None, self._bldr)

    def abort(self):
        # type: () -> None
        _apilog.logcall('abort', [self._bldr], None, self._bldr)

    def gen_sym(self, name=None):
        # type: (str) -> MuID
        name_cstr = CStr(name) if name else NULL
        res_var = CVar('MuID', 'id')
        _apilog.logcall('gen_sym', [self._bldr, name_cstr], res_var, self._bldr)
        return res_var

    def new_type_int(self, id, len):
        # type: (MuID, int) -> None
        _apilog.logcall('new_type_int', [self._bldr, id, len], None, self._bldr)

    def new_type_float(self, id):
        # type: (MuID) -> None
        _apilog.logcall('new_type_float', [self._bldr, id], None, self._bldr)

    def new_type_double(self, id):
        # type: (MuID) -> None
        _apilog.logcall('new_type_double', [self._bldr, id], None, self._bldr)

    def new_type_uptr(self, id, ty):
        # type: (MuID, MuTypeNode) -> None
        _apilog.logcall('new_type_uptr', [self._bldr, id, ty], None, self._bldr)

    def new_type_ufuncptr(self, id, sig):
        # type: (MuID, MuFuncSigNode) -> None
        _apilog.logcall('new_type_ufuncptr', [self._bldr, id, sig], None, self._bldr)

    def new_type_struct(self, id, fieldtys):
        # type: (MuID, [MuTypeNode]) -> None
        fieldtys_arr, fieldtys_sz = lst2arr('MuTypeNode', fieldtys)
        _apilog.logcall('new_type_struct', [self._bldr, id, fieldtys_arr, fieldtys_sz], None, self._bldr)

    def new_type_hybrid(self, id, fixedtys, varty):
        # type: (MuID, [MuTypeNode], MuTypeNode) -> None
        fixedtys_arr, fixedtys_sz = lst2arr('MuTypeNode', fixedtys)
        _apilog.logcall('new_type_hybrid', [self._bldr, id, fixedtys_arr, fixedtys_sz, varty], None, self._bldr)

    def new_type_array(self, id, elemty, len):
        # type: (MuID, MuTypeNode, int) -> None
        _apilog.logcall('new_type_array', [self._bldr, id, elemty, len], None, self._bldr)

    def new_type_vector(self, id, elemty, len):
        # type: (MuID, MuTypeNode, int) -> None
        _apilog.logcall('new_type_vector', [self._bldr, id, elemty, len], None, self._bldr)

    def new_type_void(self, id):
        # type: (MuID) -> None
        _apilog.logcall('new_type_void', [self._bldr, id], None, self._bldr)

    def new_type_ref(self, id, ty):
        # type: (MuID, MuTypeNode) -> None
        _apilog.logcall('new_type_ref', [self._bldr, id, ty], None, self._bldr)

    def new_type_iref(self, id, ty):
        # type: (MuID, MuTypeNode) -> None
        _apilog.logcall('new_type_iref', [self._bldr, id, ty], None, self._bldr)

    def new_type_weakref(self, id, ty):
        # type: (MuID, MuTypeNode) -> None
        _apilog.logcall('new_type_weakref', [self._bldr, id, ty], None, self._bldr)

    def new_type_funcref(self, id, sig):
        # type: (MuID, MuFuncSigNode) -> None
        _apilog.logcall('new_type_funcref', [self._bldr, id, sig], None, self._bldr)

    def new_type_tagref64(self, id):
        # type: (MuID) -> None
        _apilog.logcall('new_type_tagref64', [self._bldr, id], None, self._bldr)

    def new_type_threadref(self, id):
        # type: (MuID) -> None
        _apilog.logcall('new_type_threadref', [self._bldr, id], None, self._bldr)

    def new_type_stackref(self, id):
        # type: (MuID) -> None
        _apilog.logcall('new_type_stackref', [self._bldr, id], None, self._bldr)

    def new_type_framecursorref(self, id):
        # type: (MuID) -> None
        _apilog.logcall('new_type_framecursorref', [self._bldr, id], None, self._bldr)

    def new_type_irbuilderref(self, id):
        # type: (MuID) -> None
        _apilog.logcall('new_type_irbuilderref', [self._bldr, id], None, self._bldr)

    def new_funcsig(self, id, paramtys, rettys):
        # type: (MuID, [MuTypeNode], [MuTypeNode]) -> None
        paramtys_arr, paramtys_sz = lst2arr('MuTypeNode', paramtys)
        rettys_arr, rettys_sz = lst2arr('MuTypeNode', rettys)
        _apilog.logcall('new_funcsig', [self._bldr, id, paramtys_arr, paramtys_sz, rettys_arr, rettys_sz], None, self._bldr)

    def new_const_int(self, id, ty, value):
        # type: (MuID, MuTypeNode, int) -> None
        _apilog.logcall('new_const_int', [self._bldr, id, ty, value], None, self._bldr)

    def new_const_int_ex(self, id, ty, values):
        # type: (MuID, MuTypeNode, [rffi.ULONG]) -> None
        values_arr, values_sz = lst2arr('uint64_t', values)
        _apilog.logcall('new_const_int_ex', [self._bldr, id, ty, values_arr, values_sz], None, self._bldr)

    def new_const_float(self, id, ty, value):
        # type: (MuID, MuTypeNode, float) -> None
        value_fltstr = '%.20f' % value
        _apilog.logcall('new_const_float', [self._bldr, id, ty, value_fltstr], None, self._bldr)

    def new_const_double(self, id, ty, value):
        # type: (MuID, MuTypeNode, float) -> None
        value_fltstr = '%.20f' % value
        _apilog.logcall('new_const_double', [self._bldr, id, ty, value_fltstr], None, self._bldr)

    def new_const_null(self, id, ty):
        # type: (MuID, MuTypeNode) -> None
        _apilog.logcall('new_const_null', [self._bldr, id, ty], None, self._bldr)

    def new_const_seq(self, id, ty, elems):
        # type: (MuID, MuTypeNode, [MuGlobalVarNode]) -> None
        elems_arr, elems_sz = lst2arr('MuGlobalVarNode', elems)
        _apilog.logcall('new_const_seq', [self._bldr, id, ty, elems_arr, elems_sz], None, self._bldr)

    def new_const_extern(self, id, ty, symbol):
        # type: (MuID, MuTypeNode, str) -> None
        symbol_cstr = CStr(symbol) if symbol else NULL
        _apilog.logcall('new_const_extern', [self._bldr, id, ty, symbol_cstr], None, self._bldr)

    def new_global_cell(self, id, ty):
        # type: (MuID, MuTypeNode) -> None
        _apilog.logcall('new_global_cell', [self._bldr, id, ty], None, self._bldr)

    def new_func(self, id, sig):
        # type: (MuID, MuFuncSigNode) -> None
        _apilog.logcall('new_func', [self._bldr, id, sig], None, self._bldr)

    def new_exp_func(self, id, func, callconv, cookie):
        # type: (MuID, MuFuncNode, MuFlag, MuConstNode) -> None
        _apilog.logcall('new_exp_func', [self._bldr, id, func, callconv, cookie], None, self._bldr)

    def new_func_ver(self, id, func, bbs):
        # type: (MuID, MuFuncNode, [MuBBNode]) -> None
        bbs_arr, bbs_sz = lst2arr('MuBBNode', bbs)
        _apilog.logcall('new_func_ver', [self._bldr, id, func, bbs_arr, bbs_sz], None, self._bldr)

    def new_bb(self, id, nor_param_ids, nor_param_types, exc_param_id, insts):
        # type: (MuID, [MuID], [MuTypeNode], MuID, [MuInstNode]) -> None
        nor_param_ids_arr, nor_param_ids_sz = lst2arr('MuID', nor_param_ids)
        nor_param_types_arr, nor_param_types_sz = lst2arr('MuTypeNode', nor_param_types)
        insts_arr, insts_sz = lst2arr('MuInstNode', insts)
        _apilog.logcall('new_bb', [self._bldr, id, nor_param_ids_arr, nor_param_types_arr, nor_param_types_sz, exc_param_id, insts_arr, insts_sz], None, self._bldr)

    def new_dest_clause(self, id, dest, vars):
        # type: (MuID, MuBBNode, [MuVarNode]) -> None
        vars_arr, vars_sz = lst2arr('MuVarNode', vars)
        _apilog.logcall('new_dest_clause', [self._bldr, id, dest, vars_arr, vars_sz], None, self._bldr)

    def new_exc_clause(self, id, nor, exc):
        # type: (MuID, MuDestClause, MuDestClause) -> None
        _apilog.logcall('new_exc_clause', [self._bldr, id, nor, exc], None, self._bldr)

    def new_keepalive_clause(self, id, vars):
        # type: (MuID, [MuLocalVarNode]) -> None
        vars_arr, vars_sz = lst2arr('MuLocalVarNode', vars)
        _apilog.logcall('new_keepalive_clause', [self._bldr, id, vars_arr, vars_sz], None, self._bldr)

    def new_csc_ret_with(self, id, rettys):
        # type: (MuID, [MuTypeNode]) -> None
        rettys_arr, rettys_sz = lst2arr('MuTypeNode', rettys)
        _apilog.logcall('new_csc_ret_with', [self._bldr, id, rettys_arr, rettys_sz], None, self._bldr)

    def new_csc_kill_old(self, id):
        # type: (MuID) -> None
        _apilog.logcall('new_csc_kill_old', [self._bldr, id], None, self._bldr)

    def new_nsc_pass_values(self, id, tys, vars):
        # type: (MuID, [MuTypeNode], [MuVarNode]) -> None
        tys_arr, tys_sz = lst2arr('MuTypeNode', tys)
        vars_arr, vars_sz = lst2arr('MuVarNode', vars)
        _apilog.logcall('new_nsc_pass_values', [self._bldr, id, tys_arr, vars_arr, vars_sz], None, self._bldr)

    def new_nsc_throw_exc(self, id, exc):
        # type: (MuID, MuVarNode) -> None
        _apilog.logcall('new_nsc_throw_exc', [self._bldr, id, exc], None, self._bldr)

    def new_binop(self, id, result_id, optr, ty, opnd1, opnd2, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, MuFlag, MuTypeNode, MuVarNode, MuVarNode, MuExcClause) -> None
        _apilog.logcall('new_binop', [self._bldr, id, result_id, optr, ty, opnd1, opnd2, exc_clause], None, self._bldr)

    def new_binop_with_status(self, id, result_id, status_result_ids, optr, status_flags, ty, opnd1, opnd2, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, [MuID], MuFlag, MuBinOpStatus, MuTypeNode, MuVarNode, MuVarNode, MuExcClause) -> None
        status_result_ids_arr, status_result_ids_sz = lst2arr('MuID', status_result_ids)
        _apilog.logcall('new_binop_with_status', [self._bldr, id, result_id, status_result_ids_arr, status_result_ids_sz, optr, status_flags, ty, opnd1, opnd2, exc_clause], None, self._bldr)

    def new_cmp(self, id, result_id, optr, ty, opnd1, opnd2):
        # type: (MuID, MuID, MuFlag, MuTypeNode, MuVarNode, MuVarNode) -> None
        _apilog.logcall('new_cmp', [self._bldr, id, result_id, optr, ty, opnd1, opnd2], None, self._bldr)

    def new_conv(self, id, result_id, optr, from_ty, to_ty, opnd):
        # type: (MuID, MuID, MuFlag, MuTypeNode, MuTypeNode, MuVarNode) -> None
        _apilog.logcall('new_conv', [self._bldr, id, result_id, optr, from_ty, to_ty, opnd], None, self._bldr)

    def new_select(self, id, result_id, cond_ty, opnd_ty, cond, if_true, if_false):
        # type: (MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> None
        _apilog.logcall('new_select', [self._bldr, id, result_id, cond_ty, opnd_ty, cond, if_true, if_false], None, self._bldr)

    def new_branch(self, id, dest):
        # type: (MuID, MuDestClause) -> None
        _apilog.logcall('new_branch', [self._bldr, id, dest], None, self._bldr)

    def new_branch2(self, id, cond, if_true, if_false):
        # type: (MuID, MuVarNode, MuDestClause, MuDestClause) -> None
        _apilog.logcall('new_branch2', [self._bldr, id, cond, if_true, if_false], None, self._bldr)

    def new_switch(self, id, opnd_ty, opnd, default_dest, cases, dests):
        # type: (MuID, MuTypeNode, MuVarNode, MuDestClause, [MuConstNode], [MuDestClause]) -> None
        cases_arr, cases_sz = lst2arr('MuConstNode', cases)
        dests_arr, dests_sz = lst2arr('MuDestClause', dests)
        _apilog.logcall('new_switch', [self._bldr, id, opnd_ty, opnd, default_dest, cases_arr, dests_arr, dests_sz], None, self._bldr)

    def new_call(self, id, result_ids, sig, callee, args, exc_clause=MU_NO_ID, keepalive_clause=MU_NO_ID):
        # type: (MuID, [MuID], MuFuncSigNode, MuVarNode, [MuVarNode], MuExcClause, MuKeepaliveClause) -> None
        result_ids_arr, result_ids_sz = lst2arr('MuID', result_ids)
        args_arr, args_sz = lst2arr('MuVarNode', args)
        _apilog.logcall('new_call', [self._bldr, id, result_ids_arr, result_ids_sz, sig, callee, args_arr, args_sz, exc_clause, keepalive_clause], None, self._bldr)

    def new_tailcall(self, id, sig, callee, args):
        # type: (MuID, MuFuncSigNode, MuVarNode, [MuVarNode]) -> None
        args_arr, args_sz = lst2arr('MuVarNode', args)
        _apilog.logcall('new_tailcall', [self._bldr, id, sig, callee, args_arr, args_sz], None, self._bldr)

    def new_ret(self, id, rvs):
        # type: (MuID, [MuVarNode]) -> None
        rvs_arr, rvs_sz = lst2arr('MuVarNode', rvs)
        _apilog.logcall('new_ret', [self._bldr, id, rvs_arr, rvs_sz], None, self._bldr)

    def new_throw(self, id, exc):
        # type: (MuID, MuVarNode) -> None
        _apilog.logcall('new_throw', [self._bldr, id, exc], None, self._bldr)

    def new_extractvalue(self, id, result_id, strty, index, opnd):
        # type: (MuID, MuID, MuTypeNode, int, MuVarNode) -> None
        _apilog.logcall('new_extractvalue', [self._bldr, id, result_id, strty, index, opnd], None, self._bldr)

    def new_insertvalue(self, id, result_id, strty, index, opnd, newval):
        # type: (MuID, MuID, MuTypeNode, int, MuVarNode, MuVarNode) -> None
        _apilog.logcall('new_insertvalue', [self._bldr, id, result_id, strty, index, opnd, newval], None, self._bldr)

    def new_extractelement(self, id, result_id, seqty, indty, opnd, index):
        # type: (MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> None
        _apilog.logcall('new_extractelement', [self._bldr, id, result_id, seqty, indty, opnd, index], None, self._bldr)

    def new_insertelement(self, id, result_id, seqty, indty, opnd, index, newval):
        # type: (MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> None
        _apilog.logcall('new_insertelement', [self._bldr, id, result_id, seqty, indty, opnd, index, newval], None, self._bldr)

    def new_shufflevector(self, id, result_id, vecty, maskty, vec1, vec2, mask):
        # type: (MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> None
        _apilog.logcall('new_shufflevector', [self._bldr, id, result_id, vecty, maskty, vec1, vec2, mask], None, self._bldr)

    def new_new(self, id, result_id, allocty, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, MuTypeNode, MuExcClause) -> None
        _apilog.logcall('new_new', [self._bldr, id, result_id, allocty, exc_clause], None, self._bldr)

    def new_newhybrid(self, id, result_id, allocty, lenty, length, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuExcClause) -> None
        _apilog.logcall('new_newhybrid', [self._bldr, id, result_id, allocty, lenty, length, exc_clause], None, self._bldr)

    def new_alloca(self, id, result_id, allocty, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, MuTypeNode, MuExcClause) -> None
        _apilog.logcall('new_alloca', [self._bldr, id, result_id, allocty, exc_clause], None, self._bldr)

    def new_allocahybrid(self, id, result_id, allocty, lenty, length, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, MuTypeNode, MuTypeNode, MuVarNode, MuExcClause) -> None
        _apilog.logcall('new_allocahybrid', [self._bldr, id, result_id, allocty, lenty, length, exc_clause], None, self._bldr)

    def new_getiref(self, id, result_id, refty, opnd):
        # type: (MuID, MuID, MuTypeNode, MuVarNode) -> None
        _apilog.logcall('new_getiref', [self._bldr, id, result_id, refty, opnd], None, self._bldr)

    def new_getfieldiref(self, id, result_id, is_ptr, refty, index, opnd):
        # type: (MuID, MuID, bool, MuTypeNode, int, MuVarNode) -> None
        is_ptr_bool = 'true' if is_ptr else 'false'
        _apilog.logcall('new_getfieldiref', [self._bldr, id, result_id, is_ptr_bool, refty, index, opnd], None, self._bldr)

    def new_getelemiref(self, id, result_id, is_ptr, refty, indty, opnd, index):
        # type: (MuID, MuID, bool, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> None
        is_ptr_bool = 'true' if is_ptr else 'false'
        _apilog.logcall('new_getelemiref', [self._bldr, id, result_id, is_ptr_bool, refty, indty, opnd, index], None, self._bldr)

    def new_shiftiref(self, id, result_id, is_ptr, refty, offty, opnd, offset):
        # type: (MuID, MuID, bool, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> None
        is_ptr_bool = 'true' if is_ptr else 'false'
        _apilog.logcall('new_shiftiref', [self._bldr, id, result_id, is_ptr_bool, refty, offty, opnd, offset], None, self._bldr)

    def new_getvarpartiref(self, id, result_id, is_ptr, refty, opnd):
        # type: (MuID, MuID, bool, MuTypeNode, MuVarNode) -> None
        is_ptr_bool = 'true' if is_ptr else 'false'
        _apilog.logcall('new_getvarpartiref', [self._bldr, id, result_id, is_ptr_bool, refty, opnd], None, self._bldr)

    def new_load(self, id, result_id, is_ptr, ord, refty, loc, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, bool, MuFlag, MuTypeNode, MuVarNode, MuExcClause) -> None
        is_ptr_bool = 'true' if is_ptr else 'false'
        _apilog.logcall('new_load', [self._bldr, id, result_id, is_ptr_bool, ord, refty, loc, exc_clause], None, self._bldr)

    def new_store(self, id, is_ptr, ord, refty, loc, newval, exc_clause=MU_NO_ID):
        # type: (MuID, bool, MuFlag, MuTypeNode, MuVarNode, MuVarNode, MuExcClause) -> None
        is_ptr_bool = 'true' if is_ptr else 'false'
        _apilog.logcall('new_store', [self._bldr, id, is_ptr_bool, ord, refty, loc, newval, exc_clause], None, self._bldr)

    def new_cmpxchg(self, id, value_result_id, succ_result_id, is_ptr, is_weak, ord_succ, ord_fail, refty, loc, expected, desired, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, MuID, bool, bool, MuFlag, MuFlag, MuTypeNode, MuVarNode, MuVarNode, MuVarNode, MuExcClause) -> None
        is_ptr_bool = 'true' if is_ptr else 'false'
        is_weak_bool = 'true' if is_weak else 'false'
        _apilog.logcall('new_cmpxchg', [self._bldr, id, value_result_id, succ_result_id, is_ptr_bool, is_weak_bool, ord_succ, ord_fail, refty, loc, expected, desired, exc_clause], None, self._bldr)

    def new_atomicrmw(self, id, result_id, is_ptr, ord, optr, ref_ty, loc, opnd, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, bool, MuFlag, MuFlag, MuTypeNode, MuVarNode, MuVarNode, MuExcClause) -> None
        is_ptr_bool = 'true' if is_ptr else 'false'
        _apilog.logcall('new_atomicrmw', [self._bldr, id, result_id, is_ptr_bool, ord, optr, ref_ty, loc, opnd, exc_clause], None, self._bldr)

    def new_fence(self, id, ord):
        # type: (MuID, MuFlag) -> None
        _apilog.logcall('new_fence', [self._bldr, id, ord], None, self._bldr)

    def new_trap(self, id, result_ids, rettys, exc_clause=MU_NO_ID, keepalive_clause=MU_NO_ID):
        # type: (MuID, [MuID], [MuTypeNode], MuExcClause, MuKeepaliveClause) -> None
        result_ids_arr, result_ids_sz = lst2arr('MuID', result_ids)
        rettys_arr, rettys_sz = lst2arr('MuTypeNode', rettys)
        _apilog.logcall('new_trap', [self._bldr, id, result_ids_arr, rettys_arr, rettys_sz, exc_clause, keepalive_clause], None, self._bldr)

    def new_watchpoint(self, id, wpid, result_ids, rettys, dis, ena, exc=MU_NO_ID, keepalive_clause=MU_NO_ID):
        # type: (MuID, MuWPID, [MuID], [MuTypeNode], MuDestClause, MuDestClause, MuDestClause, MuKeepaliveClause) -> None
        result_ids_arr, result_ids_sz = lst2arr('MuID', result_ids)
        rettys_arr, rettys_sz = lst2arr('MuTypeNode', rettys)
        _apilog.logcall('new_watchpoint', [self._bldr, id, wpid, result_ids_arr, rettys_arr, rettys_sz, dis, ena, exc, keepalive_clause], None, self._bldr)

    def new_wpbranch(self, id, wpid, dis, ena):
        # type: (MuID, MuWPID, MuDestClause, MuDestClause) -> None
        _apilog.logcall('new_wpbranch', [self._bldr, id, wpid, dis, ena], None, self._bldr)

    def new_ccall(self, id, result_ids, callconv, callee_ty, sig, callee, args, exc_clause=MU_NO_ID, keepalive_clause=MU_NO_ID):
        # type: (MuID, [MuID], MuFlag, MuTypeNode, MuFuncSigNode, MuVarNode, [MuVarNode], MuExcClause, MuKeepaliveClause) -> None
        result_ids_arr, result_ids_sz = lst2arr('MuID', result_ids)
        args_arr, args_sz = lst2arr('MuVarNode', args)
        _apilog.logcall('new_ccall', [self._bldr, id, result_ids_arr, result_ids_sz, callconv, callee_ty, sig, callee, args_arr, args_sz, exc_clause, keepalive_clause], None, self._bldr)

    def new_newthread(self, id, result_id, stack, threadlocal, new_stack_clause, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, MuVarNode, MuVarNode, MuNewStackClause, MuExcClause) -> None
        _apilog.logcall('new_newthread', [self._bldr, id, result_id, stack, threadlocal, new_stack_clause, exc_clause], None, self._bldr)

    def new_swapstack(self, id, result_ids, swappee, cur_stack_clause, new_stack_clause, exc_clause=MU_NO_ID, keepalive_clause=MU_NO_ID):
        # type: (MuID, [MuID], MuVarNode, MuCurStackClause, MuNewStackClause, MuExcClause, MuKeepaliveClause) -> None
        result_ids_arr, result_ids_sz = lst2arr('MuID', result_ids)
        _apilog.logcall('new_swapstack', [self._bldr, id, result_ids_arr, result_ids_sz, swappee, cur_stack_clause, new_stack_clause, exc_clause, keepalive_clause], None, self._bldr)

    def new_comminst(self, id, result_ids, opcode, flags, tys, sigs, args, exc_clause=MU_NO_ID, keepalive_clause=MU_NO_ID):
        # type: (MuID, [MuID], MuFlag, [MuFlag], [MuTypeNode], [MuFuncSigNode], [MuVarNode], MuExcClause, MuKeepaliveClause) -> None
        result_ids_arr, result_ids_sz = lst2arr('MuID', result_ids)
        flags_arr, flags_sz = lst2arr('MuFlag', flags)
        tys_arr, tys_sz = lst2arr('MuTypeNode', tys)
        sigs_arr, sigs_sz = lst2arr('MuFuncSigNode', sigs)
        args_arr, args_sz = lst2arr('MuVarNode', args)
        _apilog.logcall('new_comminst', [self._bldr, id, result_ids_arr, result_ids_sz, opcode, flags_arr, flags_sz, tys_arr, tys_sz, sigs_arr, sigs_sz, args_arr, args_sz, exc_clause, keepalive_clause], None, self._bldr)


# -------------------------------------------------------------------------------------------------------
# Helpers
def null(rmu_t):
    return NULL

def lst2arr(c_elm_t, lst):
    sz = len(lst)
    if len(lst) > 0:
        arr = CArrayConst(c_elm_t, lst)
    else:
        arr = NULL
    return arr, sz

