"""
Implementation of bundle building API for generating a text bundle.

This file aims to be RPython compliant.
"""
from .api import *
from rpython.rlib.objectmodel import compute_unique_id


# -----------------------------------------------------------------------------
# Nodes
class MuTextIRNode(AbstractMuIRNode):
    pass


class MuTextBundleNode(MuTextIRNode):
    def __init__(self):
        self.buffer = []
        self._childnodes = dict()
        self._reftypenodes = dict()     # to be processed later

    def add_node(self, node):
        self._childnodes[node.id] = node

    def get_node(self, id):
        return self._childnodes[id]

    def add_reftypenode(self, node):
        self._reftypenodes[node.id] = node


class MuTextChildNode(MuTextIRNode):
    def __init__(self, name=None):
        self.id = compute_unique_id(self)
        self.name = name


class MuTextTypeNode(MuTextChildNode):
    def __init__(self, name=None, reftype=None, refrnt=None):
        MuTextChildNode.__init__(self, name)
        self.refrnt = refrnt
        self.reftype = reftype


class MuTextFuncSigNode(MuTextChildNode):       pass
class MuTextVarNode(MuTextChildNode):           pass
class MuTextGlobalVarNode(MuTextVarNode):       pass
class MuTextConstNode(MuTextGlobalVarNode):     pass
class MuTextGlobalNode(MuTextGlobalVarNode):    pass
class MuTextFuncNode(MuTextGlobalVarNode):      pass
class MuTextExpFuncNode(MuTextGlobalVarNode):   pass
class MuTextLocalVarNode(MuTextVarNode):        pass
class MuTextNorParamNode(MuTextLocalVarNode):   pass
class MuTextExcParamNode(MuTextLocalVarNode):   pass
class MuTextInstResNode(MuTextLocalVarNode):    pass
class MuTextFuncVerNode(MuTextChildNode):       pass
class MuTextBBNode(MuTextChildNode):            pass
class MuTextInstNode(MuTextChildNode):          pass


# -----------------------------------------------------------------------------
class MuTextBundleBuildingAPI(AbstractMuBundleBuildingAPI):
    @staticmethod
    def new_bundle():
        # type: () -> MuBundleNode
        return MuTextBundleNode()

    @staticmethod
    def abort_bundle_node(b):
        b.buffer = None

    @staticmethod
    def get_node(b, id):
        # type: (MuBundleNode, MuID) -> MuChildNode
        return b.get_node(id)

    @staticmethod
    def get_id(b, node):
        # type: (MuBundleNode, MuChildNode) -> MuID
        return node.id

    @staticmethod
    def set_name(b, node, name):
        # type: (MuBundleNode, MuChildNode, MuName) -> None
        node.name = name

    @staticmethod
    def _new_typenode(b, name, constructor):
        nd = MuTextTypeNode(name)
        b.buffer.append(".typedef @%s = %s" % (name, constructor))
        b.add_node(nd)
        return nd

    @staticmethod
    def new_type_int(b, len):
        # type: (MuBundleNode, int) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_typenode(b, "i%d" % len, "int<%d>" % len)

    @staticmethod
    def new_type_float(b):
        # type: (MuBundleNode) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_typenode(b, "flt", "float")

    @staticmethod
    def new_type_double(b):
        # type: (MuBundleNode) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_typenode(b, "dbl", "double")

    @staticmethod
    def _new_reftypenode(b, reft):
        nd = MuTextTypeNode(reftype=reft)
        b.add_reftypenode(nd)
        return nd

    @staticmethod
    def new_type_uptr(b):
        # type: (MuBundleNode) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_reftypenode(b, 'uptr')

    @staticmethod
    def set_type_uptr(uptr, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        uptr.refrnt = ty
        uptr.name = "ptr" + ty.name

    @staticmethod
    def new_type_ufuncptr(b):
        # type: (MuBundleNode) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_reftypenode(b, 'ufuncptr')

    @staticmethod
    def set_type_ufuncptr(ufuncptr, sig):
        # type: (MuTypeNode, MuFuncSigNode) -> None
        ufuncptr.refrnt = sig
        ufuncptr.name = "fnp" + sig.name

    @staticmethod
    def new_type_struct(b, fieldtys):
        # type: (MuBundleNode, [MuTypeNode]) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_typenode(b,
                                                     "stt%s" % "".join([f.name for f in fieldtys]),
                                                     "struct<%s>" % " ".join(["@" + f.name for f in fieldtys]))

    @staticmethod
    def new_type_hybrid(b, fixedtys, varty):
        # type: (MuBundleNode, [MuTypeNode], MuTypeNode) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_typenode(b,
                                                     "hyb%s%s" % ("".join([f.name for f in fixedtys]), varty),
                                                     "hybrid<%s %s>" % (
                                                         " ".join(["@" + f.name for f in fixedtys]),
                                                         "@" + varty.name))

    @staticmethod
    def new_type_array(b, elemty, len):
        # type: (MuBundleNode, MuTypeNode, uint64_t) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_typenode(b, "arr%d%s" % (len, elemty.name),
                                                     "array<%s %d>" % ("@" + elemty.name, len))

    @staticmethod
    def new_type_vector(b, elemty, len):
        # type: (MuBundleNode, MuTypeNode, uint64_t) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_typenode(b, "vec%d%s" % (len, elemty.name),
                                                     "vector<%s %d>" % ("@" + elemty.name, len))

    @staticmethod
    def new_type_void(b):
        # type: (MuBundleNode) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_typenode(b, "void", "void")

    @staticmethod
    def new_type_ref(b):
        # type: (MuBundleNode) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_reftypenode(b, 'ref')

    @staticmethod
    def set_type_ref(ref, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        ref.refrnt = ty
        ref.name = "ref" + ty.name

    @staticmethod
    def new_type_iref(b):
        # type: (MuBundleNode) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_reftypenode(b, 'iref')

    @staticmethod
    def set_type_iref(iref, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        iref.refrnt = ty
        iref.name = "iref" + ty.name

    @staticmethod
    def new_type_weakref(b):
        # type: (MuBundleNode) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_reftypenode(b, 'weakref')

    @staticmethod
    def set_type_weakref(weakref, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        weakref.refrnt = ty
        weakref.name = "wrf" + ty.name

    @staticmethod
    def new_type_funcref(b):
        # type: (MuBundleNode) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_reftypenode(b, 'funcref')

    @staticmethod
    def set_type_funcref(funcref, sig):
        # type: (MuTypeNode, MuFuncSigNode) -> None
        funcref.refrnt = sig
        funcref.name = "fnr" + sig.name

    @staticmethod
    def new_type_tagref64(b):
        # type: (MuBundleNode) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_typenode(b, "tag", "tagref64")

    @staticmethod
    def new_type_threadref(b):
        # type: (MuBundleNode) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_typenode(b, "thr", "threadref")

    @staticmethod
    def new_type_stackref(b):
        # type: (MuBundleNode) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_typenode(b, "stk", "stackref")

    @staticmethod
    def new_type_framecursorref(b):
        return MuTextBundleBuildingAPI._new_typenode(b, "fmc", "framecursorref")

    @staticmethod
    def new_type_irnoderef(b):
        # type: (MuBundleNode) -> MuTypeNode
        return MuTextBundleBuildingAPI._new_typenode(b, "ndr", "irnoderef")

    @staticmethod
    def new_funcsig(b, paramtys, rettys):
        # type: (MuBundleNode, [MuTypeNode], [MuTypeNode]) -> MuFuncSigNode
        nd = MuTextFuncSigNode("%s_%s" % ([f.name for f in paramtys], [f.name for f in rettys]))
        b.buffer.append(".funcsig %s = (%s) -> (%s)" %
                        (nd.name, ["@"+f.name for f in paramtys], ["@"+f.name for f in rettys]))
        b.add_node(nd)
        return nd

    @staticmethod
    def new_const_int(b, ty, value):
        # type: (MuBundleNode, MuTypeNode, uint64_t) -> MuConstNode
        pass

    @staticmethod
    def new_const_int_ex(b, ty, values):
        # type: (MuBundleNode, MuTypeNode, [uint64_t]) -> MuConstNode
        pass

    @staticmethod
    def new_const_float(b, ty, value):
        # type: (MuBundleNode, MuTypeNode, float) -> MuConstNode
        pass

    @staticmethod
    def new_const_double(b, ty, value):
        # type: (MuBundleNode, MuTypeNode, double) -> MuConstNode
        pass

    @staticmethod
    def new_const_null(b, ty):
        # type: (MuBundleNode, MuTypeNode) -> MuConstNode
        pass

    @staticmethod
    def new_const_seq(b, ty, elems):
        # type: (MuBundleNode, MuTypeNode, [MuConstNode]) -> MuConstNode
        pass

    @staticmethod
    def new_global_cell(b, ty):
        # type: (MuBundleNode, MuTypeNode) -> MuGlobalNode
        pass

    @staticmethod
    def new_func(b, sig):
        # type: (MuBundleNode, MuFuncSigNode) -> MuFuncNode
        pass

    @staticmethod
    def new_func_ver(b, func):
        # type: (MuBundleNode, MuFuncNode) -> MuFuncVerNode
        pass

    @staticmethod
    def new_exp_func(b, func, callconv, cookie):
        # type: (MuBundleNode, MuFuncNode, MuCallConv, MuConstNode) -> MuExpFuncNode
        pass

    @staticmethod
    def new_bb(fv):
        # type: (MuFuncVerNode) -> MuBBNode
        pass

    @staticmethod
    def new_nor_param(bb, ty):
        # type: (MuBBNode, MuTypeNode) -> MuNorParamNode
        pass

    @staticmethod
    def new_exc_param(bb):
        # type: (MuBBNode) -> MuExcParamNode
        pass

    @staticmethod
    def new_inst_res(inst):
        # type: (MuInstNode) -> MuInstResNode
        pass

    @staticmethod
    def add_dest(inst, kind, dest, vars):
        # type: (MuInstNode, MuDestKind, MuBBNode, [MuVarNode]) -> None
        pass

    @staticmethod
    def add_keepalives(inst, vars):
        # type: (MuInstNode, [MuLocalVarNode]) -> None
        pass

    @staticmethod
    def new_binop(bb, optr, ty, opnd1, opnd2):
        # type: (MuBBNode, MuBinOptr, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_cmp(bb, optr, ty, opnd1, opnd2):
        # type: (MuBBNode, MuCmpOptr, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_conv(bb, optr, from_ty, to_ty, opnd):
        # type: (MuBBNode, MuConvOptr, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_select(bb, cond_ty, opnd_ty, cond, if_true, if_false):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_branch(bb):
        # type: (MuBBNode) -> MuInstNode
        pass

    @staticmethod
    def new_branch2(bb, cond):
        # type: (MuBBNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_switch(bb, opnd_ty, opnd):
        # type: (MuBBNode, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def add_switch_dest(sw, key, dest, vars):
        # type: (MuInstNode, MuConstNode, MuBBNode, [MuVarNode]) -> None
        pass

    @staticmethod
    def new_call(bb, sig, callee, args):
        # type: (MuBBNode, MuFuncSigNode, MuVarNode, [MuVarNode]) -> MuInstNode
        pass

    @staticmethod
    def new_tailcall(bb, sig, callee, args):
        # type: (MuBBNode, MuFuncSigNode, MuVarNode, [MuVarNode]) -> MuInstNode
        pass

    @staticmethod
    def new_ret(bb, rvs):
        # type: (MuBBNode, [MuVarNode]) -> MuInstNode
        pass

    @staticmethod
    def new_throw(bb, exc):
        # type: (MuBBNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_extractvalue(bb, strty, index, opnd):
        # type: (MuBBNode, MuTypeNode, int, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_insertvalue(bb, strty, index, opnd, newval):
        # type: (MuBBNode, MuTypeNode, int, MuVarNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_extractelement(bb, seqty, indty, opnd, index):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_insertelement(bb, seqty, indty, opnd, index, newval):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_shufflevector(bb, vecty, maskty, vec1, vec2, mask):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_new(bb, allocty):
        # type: (MuBBNode, MuTypeNode) -> MuInstNode
        pass

    @staticmethod
    def new_newhybrid(bb, allocty, lenty, length):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_alloca(bb, allocty):
        # type: (MuBBNode, MuTypeNode) -> MuInstNode
        pass

    @staticmethod
    def new_allocahybrid(bb, allocty, lenty, length):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_getiref(bb, refty, opnd):
        # type: (MuBBNode, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_getfieldiref(bb, is_ptr, refty, index, opnd):
        # type: (MuBBNode, int, MuTypeNode, int, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_getelemiref(bb, is_ptr, refty, indty, opnd, index):
        # type: (MuBBNode, int, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_shiftiref(bb, is_ptr, refty, offty, opnd, offset):
        # type: (MuBBNode, int, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_getvarpartiref(bb, is_ptr, refty, opnd):
        # type: (MuBBNode, int, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_load(bb, is_ptr, ord, refty, loc):
        # type: (MuBBNode, int, MuMemOrd, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_store(bb, is_ptr, ord, refty, loc, newval):
        # type: (MuBBNode, int, MuMemOrd, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_cmpxchg(bb, is_ptr, is_weak, ord_succ, ord_fail, refty, loc, expected, desired):
        # type: (MuBBNode, int, int, MuMemOrd, MuMemOrd, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_atomicrmw(bb, is_ptr, ord, optr, refTy, loc, opnd):
        # type: (MuBBNode, int, MuMemOrd, MuAtomicRMWOp, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_fence(bb, ord):
        # type: (MuBBNode, MuMemOrd) -> MuInstNode
        pass

    @staticmethod
    def new_trap(bb, rettys):
        # type: (MuBBNode, [MuTypeNode]) -> MuInstNode
        pass

    @staticmethod
    def new_watchpoint(bb, wpid, rettys):
        # type: (MuBBNode, MuWPID, [MuTypeNode]) -> MuInstNode
        pass

    @staticmethod
    def new_wpbranch(bb, wpid):
        # type: (MuBBNode, MuWPID) -> MuInstNode
        pass

    @staticmethod
    def new_ccall(bb, callconv, callee_ty, sig, callee, args):
        # type: (MuBBNode, MuCallConv, MuTypeNode, MuFuncSigNode, MuVarNode, [MuVarNode]) -> MuInstNode
        pass

    @staticmethod
    def new_newthread(bb, stack, threadlocal):
        # type: (MuBBNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def new_swapstack_ret(bb, swappee, ret_tys):
        # type: (MuBBNode, MuVarNode, [MuTypeNode]) -> MuInstNode
        pass

    @staticmethod
    def new_swapstack_kill(bb, swappee):
        # type: (MuBBNode, MuVarNode) -> MuInstNode
        pass

    @staticmethod
    def set_newstack_pass_values(inst, tys, vars):
        # type: (MuInstNode, MuTypeNode, [MuVarNode]) -> None
        pass

    @staticmethod
    def set_newstack_throw_exc(inst, exc):
        # type: (MuInstNode, MuVarNode) -> None
        pass

    @staticmethod
    def new_comminst(bb, opcode, flags, tys, sigs, args):
        # type: (MuBBNode, MuCommInst, [MuFlag], [MuTypeNode], [MuFuncSigNode], [MuVarNode]) -> MuInstNode
        pass