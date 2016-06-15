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
    def new_bundle(self):
        # type: (AbstractMuBundleBuildingAPI) -> MuBundleNode
        pass

    def load_bundle_from_node(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> None
        pass

    def abort_bundle_node(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> None
        pass

    def get_node(self, b, id):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, MuID) -> MuChildNode
        pass

    def get_id(self, b, node):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, MuChildNode) -> MuID
        pass

    def set_name(self, b, node, name):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, MuChildNode, MuName) -> None
        pass

    def new_type_int(self, b, len):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, int) -> MuTypeNode
        pass

    def new_type_float(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> MuTypeNode
        pass

    def new_type_double(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> MuTypeNode
        pass

    def new_type_uptr(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> MuTypeNode
        pass

    def set_type_uptr(self, uptr, ty):
        # type: (AbstractMuBundleBuildingAPI, MuTypeNode, MuTypeNode) -> None
        pass

    def new_type_ufuncptr(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> MuTypeNode
        pass

    def set_type_ufuncptr(self, ufuncptr, sig):
        # type: (AbstractMuBundleBuildingAPI, MuTypeNode, MuFuncSigNode) -> None
        pass

    def new_type_struct(self, b, fieldtys):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, [MuTypeNode]) -> MuTypeNode
        pass

    def new_type_hybrid(self, b, fixedtys, varty):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, [MuTypeNode], MuTypeNode) -> MuTypeNode
        pass

    def new_type_array(self, b, elemty, len):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, MuTypeNode, uint64_t) -> MuTypeNode
        pass

    def new_type_vector(self, b, elemty, len):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, MuTypeNode, uint64_t) -> MuTypeNode
        pass

    def new_type_void(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> MuTypeNode
        pass

    def new_type_ref(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> MuTypeNode
        pass

    def set_type_ref(self, ref, ty):
        # type: (AbstractMuBundleBuildingAPI, MuTypeNode, MuTypeNode) -> None
        pass

    def new_type_iref(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> MuTypeNode
        pass

    def set_type_iref(self, iref, ty):
        # type: (AbstractMuBundleBuildingAPI, MuTypeNode, MuTypeNode) -> None
        pass

    def new_type_weakref(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> MuTypeNode
        pass

    def set_type_weakref(self, weakref, ty):
        # type: (AbstractMuBundleBuildingAPI, MuTypeNode, MuTypeNode) -> None
        pass

    def new_type_funcref(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> MuTypeNode
        pass

    def set_type_funcref(self, funcref, sig):
        # type: (AbstractMuBundleBuildingAPI, MuTypeNode, MuFuncSigNode) -> None
        pass

    def new_type_tagref64(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> MuTypeNode
        pass

    def new_type_threadref(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> MuTypeNode
        pass

    def new_type_stackref(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> MuTypeNode
        pass

    def new_type_framecursorref(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> MuTypeNode
        pass

    def new_type_irnoderef(self, b):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode) -> MuTypeNode
        pass

    def new_funcsig(self, b, paramtys, rettys):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, [MuTypeNode], [MuTypeNode]) -> MuFuncSigNode
        pass

    def new_const_int(self, b, ty, value):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, MuTypeNode, uint64_t) -> MuConstNode
        pass

    def new_const_int_ex(self, b, ty, values):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, MuTypeNode, [uint64_t]) -> MuConstNode
        pass

    def new_const_float(self, b, ty, value):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, MuTypeNode, float) -> MuConstNode
        pass

    def new_const_double(self, b, ty, value):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, MuTypeNode, double) -> MuConstNode
        pass

    def new_const_null(self, b, ty):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, MuTypeNode) -> MuConstNode
        pass

    def new_const_seq(self, b, ty, elems):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, MuTypeNode, [MuConstNode]) -> MuConstNode
        pass

    def new_global_cell(self, b, ty):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, MuTypeNode) -> MuGlobalNode
        pass

    def new_func(self, b, sig):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, MuFuncSigNode) -> MuFuncNode
        pass

    def new_func_ver(self, b, func):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, MuFuncNode) -> MuFuncVerNode
        pass

    def new_exp_func(self, b, func, callconv, cookie):
        # type: (AbstractMuBundleBuildingAPI, MuBundleNode, MuFuncNode, MuCallConv, MuConstNode) -> MuExpFuncNode
        pass

    def new_bb(self, fv):
        # type: (AbstractMuBundleBuildingAPI, MuFuncVerNode) -> MuBBNode
        pass

    def new_nor_param(self, bb, ty):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuTypeNode) -> MuNorParamNode
        pass

    def new_exc_param(self, bb):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode) -> MuExcParamNode
        pass

    def new_inst_res(self, inst):
        # type: (AbstractMuBundleBuildingAPI, MuInstNode) -> MuInstResNode
        pass

    def add_dest(self, inst, kind, dest, vars):
        # type: (AbstractMuBundleBuildingAPI, MuInstNode, MuDestKind, MuBBNode, [MuVarNode]) -> None
        pass

    def add_keepalives(self, inst, vars):
        # type: (AbstractMuBundleBuildingAPI, MuInstNode, [MuLocalVarNode]) -> None
        pass

    def new_binop(self, bb, optr, ty, opnd1, opnd2):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuBinOptr, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_cmp(self, bb, optr, ty, opnd1, opnd2):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuCmpOptr, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_conv(self, bb, optr, from_ty, to_ty, opnd):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuConvOptr, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    def new_select(self, bb, cond_ty, opnd_ty, cond, if_true, if_false):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_branch(self, bb):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode) -> MuInstNode
        pass

    def new_branch2(self, bb, cond):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuVarNode) -> MuInstNode
        pass

    def new_switch(self, bb, opnd_ty, opnd):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    def add_switch_dest(self, sw, key, dest, vars):
        # type: (AbstractMuBundleBuildingAPI, MuInstNode, MuConstNode, MuBBNode, [MuVarNode]) -> None
        pass

    def new_call(self, bb, sig, callee, args):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuFuncSigNode, MuVarNode, [MuVarNode]) -> MuInstNode
        pass

    def new_tailcall(self, bb, sig, callee, args):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuFuncSigNode, MuVarNode, [MuVarNode]) -> MuInstNode
        pass

    def new_ret(self, bb, rvs):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, [MuVarNode]) -> MuInstNode
        pass

    def new_throw(self, bb, exc):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuVarNode) -> MuInstNode
        pass

    def new_extractvalue(self, bb, strty, index, opnd):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuTypeNode, int, MuVarNode) -> MuInstNode
        pass

    def new_insertvalue(self, bb, strty, index, opnd, newval):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuTypeNode, int, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_extractelement(self, bb, seqty, indty, opnd, index):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_insertelement(self, bb, seqty, indty, opnd, index, newval):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_shufflevector(self, bb, vecty, maskty, vec1, vec2, mask):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_new(self, bb, allocty):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuTypeNode) -> MuInstNode
        pass

    def new_newhybrid(self, bb, allocty, lenty, length):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    def new_alloca(self, bb, allocty):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuTypeNode) -> MuInstNode
        pass

    def new_allocahybrid(self, bb, allocty, lenty, length):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    def new_getiref(self, bb, refty, opnd):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    def new_getfieldiref(self, bb, is_ptr, refty, index, opnd):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, int, MuTypeNode, int, MuVarNode) -> MuInstNode
        pass

    def new_getelemiref(self, bb, is_ptr, refty, indty, opnd, index):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, int, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_shiftiref(self, bb, is_ptr, refty, offty, opnd, offset):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, int, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_getvarpartiref(self, bb, is_ptr, refty, opnd):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, int, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    def new_load(self, bb, is_ptr, ord, refty, loc):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, int, MuMemOrd, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    def new_store(self, bb, is_ptr, ord, refty, loc, newval):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, int, MuMemOrd, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_cmpxchg(self, bb, is_ptr, is_weak, ord_succ, ord_fail, refty, loc, expected, desired):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, int, int, MuMemOrd, MuMemOrd, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_atomicrmw(self, bb, is_ptr, ord, optr, refTy, loc, opnd):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, int, MuMemOrd, MuAtomicRMWOp, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_fence(self, bb, ord):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuMemOrd) -> MuInstNode
        pass

    def new_trap(self, bb, rettys):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, [MuTypeNode]) -> MuInstNode
        pass

    def new_watchpoint(self, bb, wpid, rettys):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuWPID, [MuTypeNode]) -> MuInstNode
        pass

    def new_wpbranch(self, bb, wpid):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuWPID) -> MuInstNode
        pass

    def new_ccall(self, bb, callconv, callee_ty, sig, callee, args):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuCallConv, MuTypeNode, MuFuncSigNode, MuVarNode, [MuVarNode]) -> MuInstNode
        pass

    def new_newthread(self, bb, stack, threadlocal):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_swapstack_ret(self, bb, swappee, ret_tys):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuVarNode, [MuTypeNode]) -> MuInstNode
        pass

    def new_swapstack_kill(self, bb, swappee):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuVarNode) -> MuInstNode
        pass

    def set_newstack_pass_values(self, inst, tys, vars):
        # type: (AbstractMuBundleBuildingAPI, MuInstNode, MuTypeNode, [MuVarNode]) -> None
        pass

    def set_newstack_throw_exc(self, inst, exc):
        # type: (AbstractMuBundleBuildingAPI, MuInstNode, MuVarNode) -> None
        pass

    def new_comminst(self, bb, opcode, flags, tys, sigs, args):
        # type: (AbstractMuBundleBuildingAPI, MuBBNode, MuCommInst, [MuFlag], [MuTypeNode], [MuFuncSigNode], [MuVarNode]) -> MuInstNode
        pass


