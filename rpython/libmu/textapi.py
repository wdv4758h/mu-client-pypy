"""
Implementation of bundle building API for generating a text bundle.

This file aims to be RPython compliant.
"""
from .api import *
from rpython.rlib.objectmodel import compute_unique_id as id


# -----------------------------------------------------------------------------
# Nodes
class MuIRNode(AbstractMuIRNode):
    pass


class MuBundleNode(MuIRNode):
    def __init__(self):
        self.buffer = []
        self._childnodes = dict()

    def add_node(self, node):
        self._childnodes[node.id] = node
        return node

    def get_node(self, id):
        return self._childnodes[id]


def _new_name(dic, name):
    if name in dic:
        dic[name] += 1
        return "%s_%d" % (name, dic[name] - 1)
    dic[name] = 0
    return name + "_0"


class MuChildNode(MuIRNode):
    __slots__ = ('id', 'name')

    def __init__(self):
        self.id = id(self)
        cls = self.__class__
        self.name = _new_name(cls._namedic, cls._name)

    def defstr(self):
        raise NotImplementedError


class MuTypeNode(MuChildNode):
    __slots__ = ('fmt_str', 'fmt_args')
    _namedic = {}
    _name = "type"

    def __init__(self, fmt_str, fmt_args=None):
        MuChildNode.__init__(self)
        self.fmt_str = fmt_str
        self.fmt_args = fmt_args

    def __str__(self):
        return "@" + self.name

    def constr(self):
        if self.fmt_args:
            return self.fmt_str % self.fmt_args
        else:
            return self.fmt_str

    def defstr(self):
        return ".typedef @%s = %s" % (self.name, self.constr())


class MuFuncSigNode(MuChildNode):
    __slots__ = ('argnds', 'retnds')
    _namedic = {}
    _name = "sig"

    def __init__(self, argnds, retnds):
        MuChildNode.__init__(self)
        self.argnds = argnds
        self.retnds = retnds

    def __str__(self):
        return "@" + self.name

    def constr(self):
        return "(%s) -> (%s)" % (" ".join(['@' + a.name for a in self.argnds]),
                                 " ".join(['@' + r.name for r in self.retnds]))

    def defstr(self):
        return ".funcsig @%s = %s" % (self.name, self.constr())


class MuVarNode(MuChildNode):           pass
class MuGlobalVarNode(MuVarNode):       pass
class MuConstNode(MuGlobalVarNode):
    __slots__ = ("typend, value")
    _namedic = {}
    _name = "const"

    def __init__(self, typend, value, constructor=None):
        MuChildNode.__init__(self)
        self.typend = typend
        self.value = value
        self.constructor = constructor

    def constr(self):
        def _scistr(f):
            # fix case where the scientific notation doesn't contain a '.', like 1e-08
            s = str(f)
            if 'e' in s:
                i = s.index('e')
                if '.' not in s[:i]:
                    s = '%s.0%s' % (s[:i], s[i:])
            # fix infinity case
            if 'inf' in s and f > 0:
                s = '+' + s  # prepend a '+' for +inf value whose '+' sign is omitted.
            return s
        if self.constructor is None:
            type_constr = self.typend.constr()
            if type_constr == "float":
                return "%sf" % _scistr(self.value)
            elif type_constr == "double":
                return "%sd" % _scistr(self.value)
            elif type_constr[:3] == "int":
                return "%d" % int(self.value)
            else:
                return "{%s}" % " ".join(["@" + e.name for e in self.value])
        else:
            return self.constructor

    def defstr(self):
        return ".const @%s <@%s> = %s" % (self.name, self.typend.name, self.constr())


class MuGlobalNode(MuGlobalVarNode):
    __slots__ = ("typend", )
    _namedic = {}
    _name = "gcl"

    def __init__(self, typend):
        MuChildNode.__init__(self)
        self.typend = typend

    def defstr(self):
        return ".global @%s <@%s>" % (self.name, self.typend.name)


class MuFuncNode(MuGlobalVarNode):      pass
class MuExpFuncNode(MuGlobalVarNode):   pass
class MuLocalVarNode(MuVarNode):        pass
class MuNorParamNode(MuLocalVarNode):   pass
class MuExcParamNode(MuLocalVarNode):   pass
class MuInstResNode(MuLocalVarNode):    pass
class MuFuncVerNode(MuChildNode):       pass
class MuBBNode(MuChildNode):            pass
class MuInstNode(MuChildNode):          pass


# -----------------------------------------------------------------------------
class MuBundleBuildingAPI(AbstractMuBundleBuildingAPI):
    @staticmethod
    def new_bundle():
        # type: () -> MuBundleNode
        return MuBundleNode()

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
    def new_type_int(b, len):
        # type: (MuBundleNode, int) -> MuTypeNode
        return b.add_node(MuTypeNode("int<%d>", (len, )))

    @staticmethod
    def new_type_float(b):
        # type: (MuBundleNode) -> MuTypeNode
        return b.add_node(MuTypeNode("float"))

    @staticmethod
    def new_type_double(b):
        # type: (MuBundleNode) -> MuTypeNode
        return b.add_node(MuTypeNode("double"))

    @staticmethod
    def new_type_uptr(b):
        # type: (MuBundleNode) -> MuTypeNode
        return b.add_node(MuTypeNode("uptr<%s>"))

    @staticmethod
    def set_type_uptr(uptr, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        uptr.fmt_args = ("@" + ty.name, )

    @staticmethod
    def new_type_ufuncptr(b):
        # type: (MuBundleNode) -> MuTypeNode
        return b.add_node(MuTypeNode("ufuncptr<%s>"))

    @staticmethod
    def set_type_ufuncptr(ufuncptr, sig):
        # type: (MuTypeNode, MuFuncSigNode) -> None
        ufuncptr.fmt_args = ("@" + sig.name, )

    @staticmethod
    def new_type_struct(b, fieldtys):
        # type: (MuBundleNode, [MuTypeNode]) -> MuTypeNode
        return b.add_node(MuTypeNode("struct<%s>", " ".join(["@" + f.name for f in fieldtys])))

    @staticmethod
    def new_type_hybrid(b, fixedtys, varty):
        # type: (MuBundleNode, [MuTypeNode], MuTypeNode) -> MuTypeNode
        return b.add_node(MuTypeNode("hybrid<%s %s>", (" ".join(["@" + f.name for f in fixedtys]),
                                                           "@" + varty.name)))

    @staticmethod
    def new_type_array(b, elemty, len):
        # type: (MuBundleNode, MuTypeNode, uint64_t) -> MuTypeNode
        return b.add_node(MuTypeNode("array<%s %d>", ("@" + elemty.name, len)))

    @staticmethod
    def new_type_vector(b, elemty, len):
        # type: (MuBundleNode, MuTypeNode, uint64_t) -> MuTypeNode
        return b.add_node(MuTypeNode("vector<%s %d>", ("@" + elemty.name, len)))

    @staticmethod
    def new_type_void(b):
        # type: (MuBundleNode) -> MuTypeNode
        return b.add_node(MuTypeNode("void"))

    @staticmethod
    def new_type_ref(b):
        # type: (MuBundleNode) -> MuTypeNode
        return b.add_node(MuTypeNode("ref<%s>"))

    @staticmethod
    def set_type_ref(ref, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        ref.fmt_args = ("@" + ty.name, )

    @staticmethod
    def new_type_iref(b):
        # type: (MuBundleNode) -> MuTypeNode
        return b.add_node(MuTypeNode("iref<%s>"))

    @staticmethod
    def set_type_iref(iref, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        iref.fmt_args = ("@" + ty.name,)

    @staticmethod
    def new_type_weakref(b):
        # type: (MuBundleNode) -> MuTypeNode
        return b.add_node(MuTypeNode("weakref<%s>"))

    @staticmethod
    def set_type_weakref(weakref, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        weakref.fmt_args = ("@" + ty.name,)

    @staticmethod
    def new_type_funcref(b):
        # type: (MuBundleNode) -> MuTypeNode
        return b.add_node(MuTypeNode("funcref<%s>"))

    @staticmethod
    def set_type_funcref(funcref, sig):
        # type: (MuTypeNode, MuFuncSigNode) -> None
        funcref.fmt_args = ("@" + sig.name,)

    @staticmethod
    def new_type_tagref64(b):
        # type: (MuBundleNode) -> MuTypeNode
        return b.add_node(MuTypeNode("tagref64"))

    @staticmethod
    def new_type_threadref(b):
        # type: (MuBundleNode) -> MuTypeNode
        return b.add_node(MuTypeNode("threadref"))

    @staticmethod
    def new_type_stackref(b):
        # type: (MuBundleNode) -> MuTypeNode
        return b.add_node(MuTypeNode("stackref"))

    @staticmethod
    def new_type_framecursorref(b):
        return b.add_node(MuTypeNode("framecursorref"))

    @staticmethod
    def new_type_irnoderef(b):
        # type: (MuBundleNode) -> MuTypeNode
        return b.add_node(MuTypeNode("irnoderef"))

    @staticmethod
    def new_funcsig(b, paramtys, rettys):
        # type: (MuBundleNode, [MuTypeNode], [MuTypeNode]) -> MuFuncSigNode
        nd = MuFuncSigNode(paramtys, rettys)
        return b.add_node(nd)

    @staticmethod
    def new_const_int(b, ty, value):
        # type: (MuBundleNode, MuTypeNode, uint64_t) -> MuConstNode
        return b.add_node(MuConstNode(ty, value))

    @staticmethod
    def new_const_int_ex(b, ty, values):
        # type: (MuBundleNode, MuTypeNode, [uint64_t]) -> MuConstNode
        raise NotImplementedError("'new_const_int_ex' not yet supported.")

    @staticmethod
    def new_const_float(b, ty, value):
        # type: (MuBundleNode, MuTypeNode, float) -> MuConstNode
        return b.add_node(MuConstNode(ty, value))

    @staticmethod
    def new_const_double(b, ty, value):
        # type: (MuBundleNode, MuTypeNode, double) -> MuConstNode
        return b.add_node(MuConstNode(ty, value))

    @staticmethod
    def new_const_null(b, ty):
        # type: (MuBundleNode, MuTypeNode) -> MuConstNode
        constr = "0" if ty.name[:3] in ("ptr", "fnp") else "0"
        return b.add_node(MuConstNode(ty, None, constr))

    @staticmethod
    def new_const_seq(b, ty, elems):
        # type: (MuBundleNode, MuTypeNode, [MuConstNode]) -> MuConstNode
        return b.add_node(MuConstNode(ty, elems))

    @staticmethod
    def new_global_cell(b, ty):
        # type: (MuBundleNode, MuTypeNode) -> MuGlobalNode
        return b.add_node(MuGlobalNode(ty))

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