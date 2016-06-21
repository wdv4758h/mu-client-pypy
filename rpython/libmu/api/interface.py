"""
Reflection of the C API to RPython.
It lays out the essential interface,
and concrete implementations need to be made with respect to it.

At this moment I can envision three implementations:
- JIT: eventually translates the method calls into corresponding COMMINSTs. (RPython)
- Image writer (not implemented): using ctypes to call into IW and writes out an executable. (Python)
- Text bundle: generate a text form bundle in the end. (Python)

This interface is in RPython.
"""


# --------------------------------
# Flags
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
class MuAtomicRMWOp:
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
class MuFlag:
    MU_CC_DEFAULT = 0x00


"""
Node type hierarchy:

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

class AbstractMuIRNode(object):                 pass
class AbstractMuBundleNode(AbstractMuIRNode):           pass
class AbstractMuChildNode(AbstractMuIRNode):            pass
class AbstractMuTypeNode(AbstractMuChildNode):          pass
class AbstractMuFuncSigNode(AbstractMuChildNode):       pass
class AbstractMuVarNode(AbstractMuChildNode):           pass
class AbstractMuGlobalVarNode(AbstractMuVarNode):       pass
class AbstractMuConstNode(AbstractMuGlobalVarNode):     pass
class AbstractMuGlobalNode(AbstractMuGlobalVarNode):    pass
class AbstractMuFuncNode(AbstractMuGlobalVarNode):      pass
class AbstractMuExpFuncNode(AbstractMuGlobalVarNode):   pass
class AbstractMuLocalVarNode(AbstractMuVarNode):        pass
class AbstractMuNorParamNode(AbstractMuLocalVarNode):   pass
class AbstractMuExcParamNode(AbstractMuLocalVarNode):   pass
class AbstractMuInstResNode(AbstractMuLocalVarNode):    pass
class AbstractMuFuncVerNode(AbstractMuChildNode):       pass
class AbstractMuBBNode(AbstractMuChildNode):            pass
class AbstractMuInstNode(AbstractMuChildNode):          pass


# --------------------------------
# Classes
class AbstractMuBundleBuildingAPI:
    @staticmethod
    def new_bundle():
        # type: () -> MuBundleNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def load_bundle_from_node(b):
        # type: (MuBundleNode) -> None
        raise NotImplementedError("abstract base")

    @staticmethod
    def abort_bundle_node(b):
        # type: (MuBundleNode) -> None
        raise NotImplementedError("abstract base")

    @staticmethod
    def get_node(b, id):
        # type: (MuBundleNode, MuID) -> MuChildNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def get_id(b, node):
        # type: (MuBundleNode, MuChildNode) -> MuID
        raise NotImplementedError("abstract base")

    @staticmethod
    def set_name(b, node, name):
        # type: (MuBundleNode, MuChildNode, MuName) -> None
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_int(b, len):
        # type: (MuBundleNode, int) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_float(b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_double(b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_uptr(b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def set_type_uptr(uptr, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_ufuncptr(b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def set_type_ufuncptr(ufuncptr, sig):
        # type: (MuTypeNode, MuFuncSigNode) -> None
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_struct(b, fieldtys):
        # type: (MuBundleNode, [MuTypeNode]) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_hybrid(b, fixedtys, varty):
        # type: (MuBundleNode, [MuTypeNode], MuTypeNode) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_array(b, elemty, len):
        # type: (MuBundleNode, MuTypeNode, uint64_t) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_vector(b, elemty, len):
        # type: (MuBundleNode, MuTypeNode, uint64_t) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_void(b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_ref(b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def set_type_ref(ref, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_iref(b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def set_type_iref(iref, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_weakref(b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def set_type_weakref(weakref, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_funcref(b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def set_type_funcref(funcref, sig):
        # type: (MuTypeNode, MuFuncSigNode) -> None
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_tagref64(b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_threadref(b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_stackref(b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_framecursorref(b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_type_irnoderef(b):
        # type: (MuBundleNode) -> MuTypeNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_funcsig(b, paramtys, rettys):
        # type: (MuBundleNode, [MuTypeNode], [MuTypeNode]) -> MuFuncSigNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_const_int(b, ty, value):
        # type: (MuBundleNode, MuTypeNode, uint64_t) -> MuConstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_const_int_ex(b, ty, values):
        # type: (MuBundleNode, MuTypeNode, [uint64_t]) -> MuConstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_const_float(b, ty, value):
        # type: (MuBundleNode, MuTypeNode, float) -> MuConstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_const_double(b, ty, value):
        # type: (MuBundleNode, MuTypeNode, double) -> MuConstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_const_null(b, ty):
        # type: (MuBundleNode, MuTypeNode) -> MuConstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_const_seq(b, ty, elems):
        # type: (MuBundleNode, MuTypeNode, [MuConstNode]) -> MuConstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_global_cell(b, ty):
        # type: (MuBundleNode, MuTypeNode) -> MuGlobalNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_func(b, sig):
        # type: (MuBundleNode, MuFuncSigNode) -> MuFuncNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_func_ver(b, func):
        # type: (MuBundleNode, MuFuncNode) -> MuFuncVerNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_exp_func(b, func, callconv, cookie):
        # type: (MuBundleNode, MuFuncNode, MuCallConv, MuConstNode) -> MuExpFuncNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_bb(fv):
        # type: (MuFuncVerNode) -> MuBBNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_nor_param(bb, ty):
        # type: (MuBBNode, MuTypeNode) -> MuNorParamNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_exc_param(bb):
        # type: (MuBBNode) -> MuExcParamNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_inst_res(inst):
        # type: (MuInstNode) -> MuInstResNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def add_dest(inst, kind, dest, vars):
        # type: (MuInstNode, MuDestKind, MuBBNode, [MuVarNode]) -> None
        raise NotImplementedError("abstract base")

    @staticmethod
    def add_keepalives(inst, vars):
        # type: (MuInstNode, [MuLocalVarNode]) -> None
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_binop(bb, optr, ty, opnd1, opnd2):
        # type: (MuBBNode, MuBinOptr, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_cmp(bb, optr, ty, opnd1, opnd2):
        # type: (MuBBNode, MuCmpOptr, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_conv(bb, optr, from_ty, to_ty, opnd):
        # type: (MuBBNode, MuConvOptr, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_select(bb, cond_ty, opnd_ty, cond, if_true, if_false):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_branch(bb):
        # type: (MuBBNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_branch2(bb, cond):
        # type: (MuBBNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_switch(bb, opnd_ty, opnd):
        # type: (MuBBNode, MuTypeNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def add_switch_dest(sw, key, dest, vars):
        # type: (MuInstNode, MuConstNode, MuBBNode, [MuVarNode]) -> None
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_call(bb, sig, callee, args):
        # type: (MuBBNode, MuFuncSigNode, MuVarNode, [MuVarNode]) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_tailcall(bb, sig, callee, args):
        # type: (MuBBNode, MuFuncSigNode, MuVarNode, [MuVarNode]) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_ret(bb, rvs):
        # type: (MuBBNode, [MuVarNode]) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_throw(bb, exc):
        # type: (MuBBNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_extractvalue(bb, strty, index, opnd):
        # type: (MuBBNode, MuTypeNode, int, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_insertvalue(bb, strty, index, opnd, newval):
        # type: (MuBBNode, MuTypeNode, int, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_extractelement(bb, seqty, indty, opnd, index):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_insertelement(bb, seqty, indty, opnd, index, newval):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_shufflevector(bb, vecty, maskty, vec1, vec2, mask):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_new(bb, allocty):
        # type: (MuBBNode, MuTypeNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_newhybrid(bb, allocty, lenty, length):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_alloca(bb, allocty):
        # type: (MuBBNode, MuTypeNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_allocahybrid(bb, allocty, lenty, length):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_getiref(bb, refty, opnd):
        # type: (MuBBNode, MuTypeNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_getfieldiref(bb, is_ptr, refty, index, opnd):
        # type: (MuBBNode, int, MuTypeNode, int, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_getelemiref(bb, is_ptr, refty, indty, opnd, index):
        # type: (MuBBNode, int, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_shiftiref(bb, is_ptr, refty, offty, opnd, offset):
        # type: (MuBBNode, int, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_getvarpartiref(bb, is_ptr, refty, opnd):
        # type: (MuBBNode, int, MuTypeNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_load(bb, is_ptr, ord, refty, loc):
        # type: (MuBBNode, int, MuMemOrd, MuTypeNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_store(bb, is_ptr, ord, refty, loc, newval):
        # type: (MuBBNode, int, MuMemOrd, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_cmpxchg(bb, is_ptr, is_weak, ord_succ, ord_fail, refty, loc, expected, desired):
        # type: (MuBBNode, int, int, MuMemOrd, MuMemOrd, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_atomicrmw(bb, is_ptr, ord, optr, refTy, loc, opnd):
        # type: (MuBBNode, int, MuMemOrd, MuAtomicRMWOp, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_fence(bb, ord):
        # type: (MuBBNode, MuMemOrd) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_trap(bb, rettys):
        # type: (MuBBNode, [MuTypeNode]) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_watchpoint(bb, wpid, rettys):
        # type: (MuBBNode, MuWPID, [MuTypeNode]) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_wpbranch(bb, wpid):
        # type: (MuBBNode, MuWPID) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_ccall(bb, callconv, callee_ty, sig, callee, args):
        # type: (MuBBNode, MuCallConv, MuTypeNode, MuFuncSigNode, MuVarNode, [MuVarNode]) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_newthread(bb, stack, threadlocal):
        # type: (MuBBNode, MuVarNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_swapstack_ret(bb, swappee, ret_tys):
        # type: (MuBBNode, MuVarNode, [MuTypeNode]) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_swapstack_kill(bb, swappee):
        # type: (MuBBNode, MuVarNode) -> MuInstNode
        raise NotImplementedError("abstract base")

    @staticmethod
    def set_newstack_pass_values(inst, tys, vars):
        # type: (MuInstNode, MuTypeNode, [MuVarNode]) -> None
        raise NotImplementedError("abstract base")

    @staticmethod
    def set_newstack_throw_exc(inst, exc):
        # type: (MuInstNode, MuVarNode) -> None
        raise NotImplementedError("abstract base")

    @staticmethod
    def new_comminst(bb, opcode, flags, tys, sigs, args):
        # type: (MuBBNode, MuCommInst, [MuFlag], [MuTypeNode], [MuFuncSigNode], [MuVarNode]) -> MuInstNode
        raise NotImplementedError("abstract base")


