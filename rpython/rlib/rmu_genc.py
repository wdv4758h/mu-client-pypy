"""
Minimal API required to compile factorial program
(target_rmu_genc_bundlebuilding.py)

MuVM.__init__
    .new_context
    .close
MuCtx.__init__
     .new_ir_builder
     .handle_from_func
     .make_boot_image
MuIRBuilder.__init__
           .gen_sym
           .new_type_int
           .new_type_uptr
           .new_const_int
           .new_global_cell
           .new_funcsig
           .new_func
           .new_func_ver
           .new_bb
           .new_cmp
           .new_binop
           .new_dest_clause
           .new_branch2
           .new_call
           .new_branch
           .new_ret
           .new_store
           .new_comminst
           .load
Flags:
    MuMemOrd.NOT_ATOMIC
    MuCmpOptr.EQ
    MuBinOptr.OR
             .SUB
             .MUL
    MuCommInst.THREAD_EXIT
    MU_NO_ID
Types:
    MuValue = rffi.VOIDP
    MuStackRefValue
    MuRefValue
Misc:
    null()

"""
from collections import OrderedDict

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype
from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rlib.objectmodel import specialize
import os

# -------------------------------------------------------------------------------------------------------
# Type definitions
MuValue = rffi.VOIDP
MuStackRefValue = MuValue
MuRefValue = MuValue

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
    EXT_PRINT_STATS = "MU_CI_UVM_EXT_PRINT_STATS"
    EXT_CLEAR_STATS = "MU_CI_UVM_EXT_CLEAR_STATS"

MU_NO_ID = "MU_NO_ID"

# -------------------------------------------------------------------------------------------------------
# OO wrappers
"""
int
#define CHECK(line) line \
    if (*muerrno) {\
        fprintf(stderr, "Line %d: Error thrown in Mu: %d\n", \
                __LINE__, *muerrno); \
        exit(1); \
    }
"""

class CCall:
    def __init__(self, fnc_name, args, rtn_var, context=None):
        self.fnc_name = fnc_name
        self.args = args
        self.rtn_var = rtn_var
        self.context = context

    def __str__(self):
        return "{rtn_stm}{ctx}{fnc}({arg_lst})".format(rtn_stm="%s = " % self.rtn_var if self.rtn_var else "",
                                                       fnc=self.fnc_name,
                                                       arg_lst=', '.join(map(str, self.args)),
                                                       ctx="%s->" % self.context if self.context else "")

    __repr__ = __str__

class CConst:
    def __init__(self, c_type, value):
        self.type = c_type
        self.value = value

    def __str__(self):
        return str(self.value)

    __repr__ = __str__

class CStr(CConst):
    def __init__(self, string):
        CConst.__init__(self, 'char*', string)

    def __str__(self):
        return '"%(value)s"' % self.__dict__

class CNULL(CConst):
    def __init__(self, c_type):
        CConst.__init__(self, c_type, None)

    def __str__(self):
        return 'NULL'

class CArrayConst(CConst):
    def __init__(self, c_elm_t, lst):
        CConst.__init__(self, '%s [%d]' % (c_elm_t, len(lst)), "{%s}" % ', '.join(map(str, lst)))

    def __str__(self):
        return "(%(type)s)%(value)s" % self.__dict__

class CVar:
    _name_dic = {}

    @staticmethod
    def new_name(base='var'):
        nd = CVar._name_dic
        if base in nd:
            count = nd[base]
            nd[base] += 1
            return "%(base)s_%(count)d" % locals()
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
        # return "(%(type)s)%(name)s" % self.__dict__
        return self.name

    __repr__ = __str__


class APILogger:
    def __init__(self):
        self.ccalls = []
        self.decl_vars = []

    def log(self, ccall):
        self.ccalls.append(ccall)
        if ccall.rtn_var:
            self.decl_vars.append(ccall.rtn_var)
    def dump(self, fp):
        fp.write('\n'
                 '// Compile with flag -std=c99\n'
                 '#include <stdio.h>\n'
                 '#include <stdlib.h>\n'
                 '#include <stdbool.h>\n'
                 '#include "muapi.h"\n'
                 '#include "refimpl2-start.h"\n')

        fp.write('int main(int argc, char** argv) {\n')
        idt = ' ' * 4
        for var in self.decl_vars:
            fp.write(idt + '%(type)s %(name)s;\n' % var.__dict__)

        for ccall in self.ccalls:
            fp.write(idt + str(ccall) + ';\n')
        fp.write('}\n')
apilog = APILogger()


class MuVM:
    def __init__(self, config_str=""):
        self._mu = CVar("MuVM*", "mu")
        apilog.log(CCall("mu_refimpl2_new_ex", [CStr(config_str)], self._mu))

    def new_context(self):
        # type: () -> MuCtx
        ctx = CVar("MuCtx*", "ctx")
        apilog.log(CCall("new_context", [self._mu], ctx, self._mu))
        return MuCtx(ctx)

    def close(self):
        apilog.log(CCall("mu_refimpl2_close", [self._mu], None))

class MuCtx:
    def __init__(self, ctx_var):
        self._ctx = ctx_var

    def handle_from_func(self, id):
        # type: (MuID) -> MuFuncRefValue
        id_var = CVar("MuFuncRefValue", "reffnc")
        apilog.log(CCall("handle_from_func", [self._ctx, id], id_var, self._ctx))
        return id_var

    def new_ir_builder(self):
        # type: () -> MuIRBuilder
        bldr = CVar("MuIRBuilder*", "bldr")
        apilog.log(CCall('new_ir_builder', [self._ctx], bldr, self._ctx))
        return MuIRBuilder(bldr)

    def make_boot_image(self, whitelist, primordial_func, primordial_stack, primordial_threadlocal, sym_fields, sym_strings, reloc_fields, reloc_strings, output_file):
        # type: ([MuID], MuFuncRefValue, MuStackRefValue, MuRefValue, [MuIRefValue], [MuCString], [MuIRefValue], [MuCString], str) -> None
        whitelist_arr, whitelist_sz = lst2arr('MuID', whitelist)
        sym_fields_arr, sym_fields_sz = lst2arr('MuIRefValue', sym_fields)
        sym_strings_arr, sym_strings_sz = lst2arr('MuCString', sym_strings)
        reloc_fields_arr, reloc_fields_sz = lst2arr('MuIRefValue', reloc_fields)
        reloc_strings_arr, reloc_strings_sz = lst2arr('MuCString', reloc_strings)
        apilog.log(CCall('make_boot_image', [self._ctx,
                                             whitelist_arr, whitelist_sz,
                                             primordial_func,
                                             CConst('MuStackRefValue', primordial_stack) if primordial_stack else CNULL('MuStackRefValue'),
                                             CConst('MuRefValue', primordial_stack) if primordial_threadlocal else CNULL('MuRefValue'),
                                             sym_fields_arr, sym_strings_arr, sym_strings_sz,
                                             reloc_fields_arr, reloc_strings_arr, reloc_strings_sz, CStr(output_file)],
                         None, self._ctx))



class MuIRBuilder:
    def __init__(self, bldr_var):
        self._bldr = bldr_var

    def load(self):
        # type: () -> None
        apilog.log(CCall('load', [self._bldr], None, self._bldr))

    def gen_sym(self, name=None):
        # type: (str) -> MuID
        var_id = CVar('MuID', 'id')
        apilog.log(CCall('gen_sym', [self._bldr, CStr(name) if name else CNULL('char*')], var_id, self._bldr))
        return var_id

    def new_type_int(self, id, len):
        # type: (MuID, int) -> None
        apilog.log(CCall('new_type_int', [self._bldr, CConst('MuID', id), CConst('int', len)], None, self._bldr))

    def new_type_uptr(self, id, ty):
        # type: (MuID, MuTypeNode) -> None
        apilog.log(CCall('new_type_uptr', [self._bldr, CConst('MuID', id), CConst('MuTypeNode', ty)], None, self._bldr))

    def new_funcsig(self, id, paramtys, rettys):
        # type: (MuID, [MuTypeNode], [MuTypeNode]) -> None
        paramtys_arr, paramtys_sz = lst2arr('MuTypeNode', paramtys)
        rettys_arr, rettys_sz = lst2arr('MuTypeNode', rettys)
        apilog.log(CCall('new_funcsig', [self._bldr, CConst('MuID', id),
                                         paramtys_arr, paramtys_sz, rettys_arr, rettys_sz],
                         None, self._bldr))

    def new_const_int(self, id, ty, value):
        # type: (MuID, MuTypeNode, int) -> None
        apilog.log(CCall('new_const_int', [self._bldr, CConst('MuID', id),
                                           CConst('MuTypeNode', ty), CConst('int', value)],
                         None, self._bldr))

    def new_global_cell(self, id, ty):
        # type: (MuID, MuTypeNode) -> None
        apilog.log(CCall('new_global_cell', [self._bldr, CConst('MuID', id), CConst('MuTypeNode', ty)], None, self._bldr))

    def new_func(self, id, sig):
        # type: (MuID, MuFuncSigNode) -> None
        apilog.log(CCall('new_func', [self._bldr, CConst('MuID', id), CConst('MuFuncSigNode', sig)], None, self._bldr))

    def new_func_ver(self, id, func, bbs):
        # type: (MuID, MuFuncNode, [MuBBNode]) -> None
        bbs_arr, bbs_sz = lst2arr('MuBBNode', bbs)
        apilog.log(CCall('new_func_ver', [self._bldr, CConst('MuID', id), CConst('MuFuncNode', func), bbs_arr, bbs_sz],
                         None, self._bldr))

    def new_bb(self, id, nor_param_ids, nor_param_types, exc_param_id, insts):
        # type: (MuID, [MuID], [MuTypeNode], MuID, [MuInstNode]) -> None
        nor_param_ids_arr, nor_param_ids_sz = lst2arr('MuID', nor_param_ids)
        nor_param_types_arr, nor_param_types_sz = lst2arr('MuTypeNode', nor_param_types)
        insts_arr, insts_sz = lst2arr('MuInstNode', insts)
        apilog.log(CCall('new_bb', [self._bldr, CConst('MuID', id),
                                    nor_param_ids_arr, nor_param_types_arr, nor_param_types_sz,
                                    CConst('MuID', exc_param_id), insts_arr, insts_sz],
                         None, self._bldr))

    def new_dest_clause(self, id, dest, vars):
        # type: (MuID, MuBBNode, [MuVarNode]) -> None
        vars_arr, vars_sz = lst2arr('MuVarNode', vars)
        apilog.log(CCall('new_dest_clause', [self._bldr, CConst('MuID', id), CConst('MuBBNode', dest), vars_arr, vars_sz],
                         None, self._bldr))

    def new_binop(self, id, result_id, optr, ty, opnd1, opnd2, exc_clause=MU_NO_ID):
        # type: (MuID, MuID, MuFlag, MuTypeNode, MuVarNode, MuVarNode, MuExcClause) -> None
        apilog.log(CCall('new_binop', [self._bldr, CConst('MuID', id), CConst('MuID', result_id), CConst('MuFlag', optr),
                                       CConst('MuTypeNode', ty), CConst('MuVarNode', opnd1), CConst('MuVarNode', opnd2),
                                       CConst('MuExcClause', exc_clause)],
                         None, self._bldr))

    def new_cmp(self, id, result_id, optr, ty, opnd1, opnd2):
        # type: (MuID, MuID, MuFlag, MuTypeNode, MuVarNode, MuVarNode) -> None
        apilog.log(CCall('new_cmp', [self._bldr, CConst('MuID', id), CConst('MuID', result_id), CConst('MuFlag', optr),
                                     CConst('MuTypeNode', ty), CConst('MuVarNode', opnd1), CConst('MuVarNode', opnd2)],
                         None, self._bldr))

    def new_branch(self, id, dest):
        # type: (MuID, MuDestClause) -> None
        apilog.log(CCall('new_branch', [self._bldr, CConst('MuID', id), CConst('MuDestClause', dest)], None, self._bldr))

    def new_branch2(self, id, cond, if_true, if_false):
        # type: (MuID, MuVarNode, MuDestClause, MuDestClause) -> None
        apilog.log(CCall('new_branch2', [self._bldr, CConst('MuID', id), CConst('MuVarNode', cond),
                                         CConst('MuDestClause', if_true), CConst('MuDestClause', if_false)],
                         None, self._bldr))

    def new_call(self, id, result_ids, sig, callee, args, exc_clause=MU_NO_ID, keepalive_clause=MU_NO_ID):
        # type: (MuID, [MuID], MuFuncSigNode, MuVarNode, [MuVarNode], MuExcClause, MuKeepaliveClause) -> None
        result_ids_arr, result_ids_sz = lst2arr('MuID', result_ids)
        args_arr, args_sz = lst2arr('MuVarNode', args)
        apilog.log(CCall('new_call', [self._bldr, CConst('MuID', id),
                                      result_ids_arr, result_ids_sz,
                                      CConst('MuFuncSigNode', sig), CConst('MuVarNode', callee),
                                      args_arr, args_sz,
                                      CConst('MuExcClause', exc_clause), CConst('MuKeepaliveClause', keepalive_clause)],
                         None, self._bldr))

    def new_ret(self, id, rvs):
        # type: (MuID, [MuVarNode]) -> None
        rvs_arr, rvs_sz = lst2arr('MuVarNode', rvs)
        apilog.log(CCall('new_ret', [self._bldr, CConst('MuID', id), rvs_arr, rvs_sz], None, self._bldr))

    def new_store(self, id, is_ptr, ord, refty, loc, newval, exc_clause=MU_NO_ID):
        # type: (MuID, bool, MuFlag, MuTypeNode, MuVarNode, MuVarNode, MuExcClause) -> None
        apilog.log(CCall('new_store', [self._bldr, CConst('MuID', id), CConst('bool', 'true' if is_ptr else 'false'),
                                       CConst('MuFlag', ord), CConst('MuTypeNode', refty),
                                       CConst('MuVarNode', loc), CConst('MuVarNode', newval),
                                       CConst('MuExcClause', exc_clause)],
                         None, self._bldr))

    def new_comminst(self, id, result_ids, opcode, flags, tys, sigs, args, exc_clause=MU_NO_ID, keepalive_clause=MU_NO_ID):
        # type: (MuID, [MuID], MuFlag, [MuFlag], [MuTypeNode], [MuFuncSigNode], [MuVarNode], MuExcClause, MuKeepaliveClause) -> None
        result_ids_arr, result_ids_sz = lst2arr('MuID', result_ids)
        flags_arr, flags_sz = lst2arr('MuFlag', flags)
        tys_arr, tys_sz = lst2arr('MuTypeNode', tys)
        sigs_arr, sigs_sz = lst2arr('MuFuncSigNode', sigs)
        args_arr, args_sz = lst2arr('MuVarNode', args)
        apilog.log(CCall('new_comminst', [self._bldr, id, result_ids_arr, result_ids_sz, opcode, flags_arr, flags_sz, tys_arr,
                                            tys_sz, sigs_arr, sigs_sz, args_arr, args_sz, exc_clause, keepalive_clause],
                         None, self._bldr))

# -------------------------------------------------------------------------------------------------------
# Mu reference implementation functions
# mu_new = rffi.llexternal('mu_refimpl2_new', [], _MuVMPtr, compilation_info=eci)
# mu_new_ex = rffi.llexternal('mu_refimpl2_new_ex', [rffi.CCHARP], _MuVMPtr, compilation_info=eci)
# mu_close = rffi.llexternal('mu_refimpl2_close', [_MuVMPtr], lltype.Void, compilation_info=eci)

# -------------------------------------------------------------------------------------------------------
# Helpers
def null(rmu_t):
    return lltype.nullptr(rmu_t.TO)

def lst2arr(c_elm_t, lst):

    sz = CConst('int', len(lst))
    if len(lst) > 0:
        arr = CArrayConst(c_elm_t, lst)
    else:
        arr = CNULL(c_elm_t + '*')
    return arr, sz