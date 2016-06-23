"""
Mu bundle building API.

Two distinct cases to direct the API function calls:
JIT --> common instructions.
AOT --> C API calls using Python binding in Mu implementation.
"""
from rpython.rlib.objectmodel import we_are_translated

"""
Node type hierarchy (intuitively):

MuIRNode
 +-- MuBundleNode
 +-- MuChildNode
     +-- MuFuncSigNode
     +-- MuInstNode
     +-- MuVarNode
     |   +-- MuLocalVarNode
     |   |   +-- MuInstResNode
     |   |   +-- MuNorParamNode
     |   |   +-- MuExcParamNode
     |   +-- MuGlobalVarNode
     |       +-- MuExpFuncNode
     |       +-- MuConstNode
     |       +-- MuFuncNode
     |       +-- MuGlobalNode
     +-- MuTypeNode
     +-- MuFuncVerNode
     +-- MuBBNode

"""


def new_context(vmopts={}):
    """
    Calls this function to create a 'context'
    from which the rest of API calls are done.
    """
    if we_are_translated():  # JIT
        return JITContext()
    else:  # AOT
        from libmu import MuRefImpl2StartDLL
        """
        Note that you may need to use DelayedDisposer (see pythonbinding/libmu)
        Also don't forget to call close_context() at the end.
        """
        opts = {
            "vmLog": "ERROR",
            "sourceInfo": False,
            "staticCheck": True,
        }
        opts.update(vmopts)

        dll = MuRefImpl2StartDLL("libmurefimpl2start.so")
        mu = dll.mu_refimpl2_new_ex(**opts)

        return mu.new_context()


# --------------------------------
# Flags
class MuTrapHandlerResult:
    MU_THREAD_EXIT = 0x00
    MU_REBIND_PASS_VALUES = 0x01
    MU_REBIND_THROW_EXC = 0x02


class MuDestKind:
    MU_DEST_NORMAL = 0x01
    MU_DEST_EXCEPT = 0x02
    MU_DEST_TRUE = 0x03
    MU_DEST_FALSE = 0x04
    MU_DEST_DEFAULT = 0x05
    MU_DEST_DISABLED = 0x06
    MU_DEST_ENABLED = 0x07


class MuBinOptr:
    MU_BINOP_ADD = 0x01
    MU_BINOP_SUB = 0x02
    MU_BINOP_MUL = 0x03
    MU_BINOP_SDIV = 0x04
    MU_BINOP_SREM = 0x05
    MU_BINOP_UDIV = 0x06
    MU_BINOP_UREM = 0x07
    MU_BINOP_SHL = 0x08
    MU_BINOP_LSHR = 0x09
    MU_BINOP_ASHR = 0x0A
    MU_BINOP_AND = 0x0B
    MU_BINOP_OR = 0x0C
    MU_BINOP_XOR = 0x0D
    MU_BINOP_FADD = 0xB0
    MU_BINOP_FSUB = 0xB1
    MU_BINOP_FMUL = 0xB2
    MU_BINOP_FDIV = 0xB3
    MU_BINOP_FREM = 0xB4


class MuCmpOptr:
    MU_CMP_EQ = 0x20
    MU_CMP_NE = 0x21
    MU_CMP_SGE = 0x22
    MU_CMP_SGT = 0x23
    MU_CMP_SLE = 0x24
    MU_CMP_SLT = 0x25
    MU_CMP_UGE = 0x26
    MU_CMP_UGT = 0x27
    MU_CMP_ULE = 0x28
    MU_CMP_ULT = 0x29
    MU_CMP_FFALSE = 0xC0
    MU_CMP_FTRUE = 0xC1
    MU_CMP_FUNO = 0xC2
    MU_CMP_FUEQ = 0xC3
    MU_CMP_FUNE = 0xC4
    MU_CMP_FUGT = 0xC5
    MU_CMP_FUGE = 0xC6
    MU_CMP_FULT = 0xC7
    MU_CMP_FULE = 0xC8
    MU_CMP_FORD = 0xC9
    MU_CMP_FOEQ = 0xCA
    MU_CMP_FONE = 0xCB
    MU_CMP_FOGT = 0xCC
    MU_CMP_FOGE = 0xCD
    MU_CMP_FOLT = 0xCE
    MU_CMP_FOLE = 0xCF


class MuConvOptr:
    MU_CONV_TRUNC = 0x30
    MU_CONV_ZEXT = 0x31
    MU_CONV_SEXT = 0x32
    MU_CONV_FPTRUNC = 0x33
    MU_CONV_FPEXT = 0x34
    MU_CONV_FPTOUI = 0x35
    MU_CONV_FPTOSI = 0x36
    MU_CONV_UITOFP = 0x37
    MU_CONV_SITOFP = 0x38
    MU_CONV_BITCAST = 0x39
    MU_CONV_REFCAST = 0x3A
    MU_CONV_PTRCAST = 0x3B


class MuMemOrd:
    MU_ORD_NOT_ATOMIC = 0x00
    MU_ORD_RELAXED = 0x01
    MU_ORD_CONSUME = 0x02
    MU_ORD_ACQUIRE = 0x03
    MU_ORD_RELEASE = 0x04
    MU_ORD_ACQ_REL = 0x05
    MU_ORD_SEQ_CST = 0x06


class MuAtomicRMWOptr:
    MU_ARMW_XCHG = 0x00
    MU_ARMW_ADD = 0x01
    MU_ARMW_SUB = 0x02
    MU_ARMW_AND = 0x03
    MU_ARMW_NAND = 0x04
    MU_ARMW_OR = 0x05
    MU_ARMW_XOR = 0x06
    MU_ARMW_MAX = 0x07
    MU_ARMW_MIN = 0x08
    MU_ARMW_UMAX = 0x09
    MU_ARMW_UMIN = 0x0A


class MuCallConv:
    MU_CC_DEFAULT = 0x00


class MuCommInst:
    MU_CI_UVM_NEW_STACK = 0x201
    MU_CI_UVM_KILL_STACK = 0x202
    MU_CI_UVM_THREAD_EXIT = 0x203
    MU_CI_UVM_CURRENT_STACK = 0x204
    MU_CI_UVM_SET_THREADLOCAL = 0x205
    MU_CI_UVM_GET_THREADLOCAL = 0x206
    MU_CI_UVM_TR64_IS_FP = 0x211
    MU_CI_UVM_TR64_IS_INT = 0x212
    MU_CI_UVM_TR64_IS_REF = 0x213
    MU_CI_UVM_TR64_FROM_FP = 0x214
    MU_CI_UVM_TR64_FROM_INT = 0x215
    MU_CI_UVM_TR64_FROM_REF = 0x216
    MU_CI_UVM_TR64_TO_FP = 0x217
    MU_CI_UVM_TR64_TO_INT = 0x218
    MU_CI_UVM_TR64_TO_REF = 0x219
    MU_CI_UVM_TR64_TO_TAG = 0x21A
    MU_CI_UVM_FUTEX_WAIT = 0x220
    MU_CI_UVM_FUTEX_WAIT_TIMEOUT = 0x221
    MU_CI_UVM_FUTEX_WAKE = 0x222
    MU_CI_UVM_FUTEX_CMP_REQUEUE = 0x223
    MU_CI_UVM_KILL_DEPENDENCY = 0x230
    MU_CI_UVM_NATIVE_PIN = 0x240
    MU_CI_UVM_NATIVE_UNPIN = 0x241
    MU_CI_UVM_NATIVE_EXPOSE = 0x242
    MU_CI_UVM_NATIVE_UNEXPOSE = 0x243
    MU_CI_UVM_NATIVE_GET_COOKIE = 0x244
    MU_CI_UVM_META_ID_OF = 0x250
    MU_CI_UVM_META_NAME_OF = 0x251
    MU_CI_UVM_META_LOAD_BUNDLE = 0x252
    MU_CI_UVM_META_LOAD_HAIL = 0x253
    MU_CI_UVM_META_NEW_CURSOR = 0x254
    MU_CI_UVM_META_NEXT_FRAME = 0x255
    MU_CI_UVM_META_COPY_CURSOR = 0x256
    MU_CI_UVM_META_CLOSE_CURSOR = 0x257
    MU_CI_UVM_META_CUR_FUNC = 0x258
    MU_CI_UVM_META_CUR_FUNC_VER = 0x259
    MU_CI_UVM_META_CUR_INST = 0x25A
    MU_CI_UVM_META_DUMP_KEEPALIVES = 0x25B
    MU_CI_UVM_META_POP_FRAMES_TO = 0x25C
    MU_CI_UVM_META_PUSH_FRAME = 0x25D
    MU_CI_UVM_META_ENABLE_WATCHPOINT = 0x25E
    MU_CI_UVM_META_DISABLE_WATCHPOINT = 0x25F
    MU_CI_UVM_META_SET_TRAP_HANDLER = 0x260


class JITContext:
    def new_bundle(self):
        # type: () -> MuBundleNode
        raise NotImplementedError

    def load_bundle_from_node(self, b):
        # type: (MuBundleNode) -> void
        raise NotImplementedError

    def abort_bundle_node(self, b):
        # type: (MuBundleNode) -> void
        raise NotImplementedError

    def get_node(self, b, id):
        # type: (MuBundleNode, MuID) -> MuChildNode
        raise NotImplementedError

    def get_id(self, b, node):
        # type: (MuBundleNode, MuChildNode) -> MuID
        raise NotImplementedError

    def set_name(self, b, node, name):
        # type: (MuBundleNode, MuChildNode, MuName) -> void
        raise NotImplementedError

    def new_type_int(self, b, len):
        # type: (MuBundleNode, int) -> MuTypeNode
        raise NotImplementedError

    def new_type_float(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError

    def new_type_double(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError

    def new_type_uptr(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError

    def set_type_uptr(self, uptr, ty):
        # type: (MuTypeNode, MuTypeNode) -> void
        raise NotImplementedError

    def new_type_ufuncptr(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError

    def set_type_ufuncptr(self, ufuncptr, sig):
        # type: (MuTypeNode, MuFuncSigNode) -> void
        raise NotImplementedError

    def new_type_struct(self, b, fieldtys, nfieldtys):
        # type: (MuBundleNode, MuTypeNode, MuArraySize) -> MuTypeNode
        raise NotImplementedError

    def new_type_hybrid(self, b, fixedtys, nfixedtys, varty):
        # type: (MuBundleNode, MuTypeNode, MuArraySize, MuTypeNode) -> MuTypeNode
        raise NotImplementedError

    def new_type_array(self, b, elemty, len):
        # type: (MuBundleNode, MuTypeNode, uint64_t) -> MuTypeNode
        raise NotImplementedError

    def new_type_vector(self, b, elemty, len):
        # type: (MuBundleNode, MuTypeNode, uint64_t) -> MuTypeNode
        raise NotImplementedError

    def new_type_void(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError

    def new_type_ref(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError

    def set_type_ref(self, ref, ty):
        # type: (MuTypeNode, MuTypeNode) -> void
        raise NotImplementedError

    def new_type_iref(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError

    def set_type_iref(self, iref, ty):
        # type: (MuTypeNode, MuTypeNode) -> void
        raise NotImplementedError

    def new_type_weakref(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError

    def set_type_weakref(self, weakref, ty):
        # type: (MuTypeNode, MuTypeNode) -> void
        raise NotImplementedError

    def new_type_funcref(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError

    def set_type_funcref(self, funcref, sig):
        # type: (MuTypeNode, MuFuncSigNode) -> void
        raise NotImplementedError

    def new_type_tagref64(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError

    def new_type_threadref(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError

    def new_type_stackref(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError

    def new_type_framecursorref(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError

    def new_type_irnoderef(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError

    def new_funcsig(self, b, paramtys, nparamtys, rettys, nrettys):
        # type: (MuBundleNode, MuTypeNode, MuArraySize, MuTypeNode, MuArraySize) -> MuFuncSigNode
        raise NotImplementedError

    def new_const_int(self, b, ty, value):
        # type: (MuBundleNode, MuTypeNode, uint64_t) -> MuConstNode
        raise NotImplementedError

    def new_const_int_ex(self, b, ty, values, nvalues):
        # type: (MuBundleNode, MuTypeNode, uint64_t, MuArraySize) -> MuConstNode
        raise NotImplementedError

    def new_const_float(self, b, ty, value):
        # type: (MuBundleNode, MuTypeNode, float) -> MuConstNode
        raise NotImplementedError

    def new_const_double(self, b, ty, value):
        # type: (MuBundleNode, MuTypeNode, double) -> MuConstNode
        raise NotImplementedError

    def new_const_null(self, b, ty):
        # type: (MuBundleNode, MuTypeNode) -> MuConstNode
        raise NotImplementedError

    def new_const_seq(self, b, ty, elems, nelems):
        # type: (MuBundleNode, MuTypeNode, MuConstNode, MuArraySize) -> MuConstNode
        raise NotImplementedError

    def new_global_cell(self, b, ty):
        # type: (MuBundleNode, MuTypeNode) -> MuGlobalNode
        raise NotImplementedError

    def new_func(self, b, sig):
        # type: (MuBundleNode, MuFuncSigNode) -> MuFuncNode
        raise NotImplementedError

    def new_func_ver(self, b, func):
        # type: (MuBundleNode, MuFuncNode) -> MuFuncVerNode
        raise NotImplementedError

    def new_exp_func(self, b, func, callconv, cookie):
        # type: (MuBundleNode, MuFuncNode, MuCallConv, MuConstNode) -> MuExpFuncNode
        raise NotImplementedError

    def new_bb(self, fv):
        # type: (MuFuncVerNode) -> MuBBNode
        raise NotImplementedError

    def new_nor_param(self, bb, ty):
        # type: (MuBBNode, MuTypeNode) -> MuNorParamNode
        raise NotImplementedError

    def new_exc_param(self, bb):
        # type: (MuBBNode) -> MuExcParamNode
        raise NotImplementedError

    def new_inst_res(self, inst):
        # type: (MuInstNode) -> MuInstResNode
        raise NotImplementedError

    def add_dest(self, inst, kind, dest, vars, nvars):
        # type: (MuInstNode, MuDestKind, MuBBNode, MuVarNode, MuArraySize) -> void
        raise NotImplementedError

    def add_keepalives(self, inst, vars, nvars):
        # type: (MuInstNode, MuLocalVarNode, MuArraySize) -> void
        raise NotImplementedError

    def new_binop(self, bb, optr, ty, opnd1, opnd2):
        # type: (MuBBNode, MuBinOptr, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_cmp(self, bb, optr, ty, opnd1, opnd2):
        # type: (MuBBNode, MuCmpOptr, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_conv(self, bb, optr, from_ty, to_ty, opnd):
        # type: (MuBBNode, MuConvOptr, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_select(self, bb, cond_ty, opnd_ty, cond, if_true, if_false):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_branch(self, bb):
        # type: (MuBBNode) -> MuInstNode
        raise NotImplementedError

    def new_branch2(self, bb, cond):
        # type: (MuBBNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_switch(self, bb, opnd_ty, opnd):
        # type: (MuBBNode, MuTypeNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def add_switch_dest(self, sw, key, dest, vars, nvars):
        # type: (MuInstNode, MuConstNode, MuBBNode, MuVarNode, MuArraySize) -> void
        raise NotImplementedError

    def new_call(self, bb, sig, callee, args, nargs):
        # type: (MuBBNode, MuFuncSigNode, MuVarNode, MuVarNode, MuArraySize) -> MuInstNode
        raise NotImplementedError

    def new_tailcall(self, bb, sig, callee, args, nargs):
        # type: (MuBBNode, MuFuncSigNode, MuVarNode, MuVarNode, MuArraySize) -> MuInstNode
        raise NotImplementedError

    def new_ret(self, bb, rvs, nrvs):
        # type: (MuBBNode, MuVarNode, MuArraySize) -> MuInstNode
        raise NotImplementedError

    def new_throw(self, bb, exc):
        # type: (MuBBNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_extractvalue(self, bb, strty, index, opnd):
        # type: (MuBBNode, MuTypeNode, int, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_insertvalue(self, bb, strty, index, opnd, newval):
        # type: (MuBBNode, MuTypeNode, int, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_extractelement(self, bb, seqty, indty, opnd, index):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_insertelement(self, bb, seqty, indty, opnd, index, newval):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_shufflevector(self, bb, vecty, maskty, vec1, vec2, mask):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_new(self, bb, allocty):
        # type: (MuBBNode, MuTypeNode) -> MuInstNode
        raise NotImplementedError

    def new_newhybrid(self, bb, allocty, lenty, length):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_alloca(self, bb, allocty):
        # type: (MuBBNode, MuTypeNode) -> MuInstNode
        raise NotImplementedError

    def new_allocahybrid(self, bb, allocty, lenty, length):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_getiref(self, bb, refty, opnd):
        # type: (MuBBNode, MuTypeNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_getfieldiref(self, bb, is_ptr, refty, index, opnd):
        # type: (MuBBNode, MuBool, MuTypeNode, int, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_getelemiref(self, bb, is_ptr, refty, indty, opnd, index):
        # type: (MuBBNode, MuBool, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_shiftiref(self, bb, is_ptr, refty, offty, opnd, offset):
        # type: (MuBBNode, MuBool, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_getvarpartiref(self, bb, is_ptr, refty, opnd):
        # type: (MuBBNode, MuBool, MuTypeNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_load(self, bb, is_ptr, ord, refty, loc):
        # type: (MuBBNode, MuBool, MuMemOrd, MuTypeNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_store(self, bb, is_ptr, ord, refty, loc, newval):
        # type: (MuBBNode, MuBool, MuMemOrd, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_cmpxchg(self, bb, is_ptr, is_weak, ord_succ, ord_fail, refty, loc, expected, desired):
        # type: (MuBBNode, MuBool, MuBool, MuMemOrd, MuMemOrd, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_atomicrmw(self, bb, is_ptr, ord, optr, refTy, loc, opnd):
        # type: (MuBBNode, MuBool, MuMemOrd, MuAtomicRMWOptr, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_fence(self, bb, ord):
        # type: (MuBBNode, MuMemOrd) -> MuInstNode
        raise NotImplementedError

    def new_trap(self, bb, rettys, nrettys):
        # type: (MuBBNode, MuTypeNode, MuArraySize) -> MuInstNode
        raise NotImplementedError

    def new_watchpoint(self, bb, wpid, rettys, nrettys):
        # type: (MuBBNode, MuWPID, MuTypeNode, MuArraySize) -> MuInstNode
        raise NotImplementedError

    def new_wpbranch(self, bb, wpid):
        # type: (MuBBNode, MuWPID) -> MuInstNode
        raise NotImplementedError

    def new_ccall(self, bb, callconv, callee_ty, sig, callee, args, nargs):
        # type: (MuBBNode, MuCallConv, MuTypeNode, MuFuncSigNode, MuVarNode, MuVarNode, MuArraySize) -> MuInstNode
        raise NotImplementedError

    def new_newthread(self, bb, stack, threadlocal):
        # type: (MuBBNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def new_swapstack_ret(self, bb, swappee, ret_tys, nret_tys):
        # type: (MuBBNode, MuVarNode, MuTypeNode, MuArraySize) -> MuInstNode
        raise NotImplementedError

    def new_swapstack_kill(self, bb, swappee):
        # type: (MuBBNode, MuVarNode) -> MuInstNode
        raise NotImplementedError

    def set_newstack_pass_values(self, inst, tys, vars, nvars):
        # type: (MuInstNode, MuTypeNode, MuVarNode, MuArraySize) -> void
        raise NotImplementedError

    def set_newstack_throw_exc(self, inst, exc):
        # type: (MuInstNode, MuVarNode) -> void
        raise NotImplementedError

    def new_comminst(self, bb, opcode, flags, nflags, tys, ntys, sigs, nsigs, args, nargs):
        # type: (MuBBNode, MuCommInst, MuFlag, MuArraySize, MuTypeNode, MuArraySize, MuFuncSigNode, MuArraySize, MuVarNode, MuArraySize) -> MuInstNode
        raise NotImplementedError
