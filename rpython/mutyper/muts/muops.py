"""
Defines the Mu instruction set
"""
from rpython.flowspace.model import FunctionGraph, Block, Variable
from rpython.mutyper.muts.muentity import MuName
from rpython.mutyper.muts.mutype import *


# ----------------------------------------------------------------
# Basic building blocks
class DEST:
    def __init__(self, blk, args):
        self.blk = blk
        self.args = args

    @staticmethod
    def from_link(lnk):
        return DEST(lnk.target, lnk.mu_args)

    def __str__(self):
        return "%s(%s)" % (self.blk.mu_name, ' '.join([str(arg.mu_name) for arg in self.args]))

    def __repr__(self):
        return str(self)


class KEEPALIVE(object):
    def __init__(self, vs=[]):
        """
        KeepAlive clause
        :param vs: list of Variables to keep alive
        """
        self.vs = vs

    def __str__(self):
        if len(self.vs) == 0:
            return ""
        return "KEEPALIVE(%s)" % (' '.join([str(v.mu_name) for v in self.vs]))

    def __repr__(self):
        return str(self)


class EXCEPT(object):
    def __init__(self, nor=None, exc=None):
        self.nor = nor
        self.exc = exc

    def __str__(self):
        if self.nor is None and self.exc is None:
            return ""
        return "EXC(%s %s)" % (self.nor, self.exc)

    def __repr__(self):
        return str(self)


class MuOperation(object):
    def __init__(self, *args, **kwargs):
        cls = self.__class__
        self.opname = cls.__name__

        if 'result' not in kwargs or kwargs['result'] is None:
            res = Variable('rtn')
            res.mu_type = cls.__dict__['_fnc_rtntype'](args)
            if res.mu_type is not void_t:
                res.mu_name = MuName(res.name, args[0].mu_name.scope if len(args) > 0 else None)
            kwargs['result'] = res

        if 'exc' not in kwargs:
            kwargs['exc'] = EXCEPT()
        if 'ka' not in kwargs:
            kwargs['ka'] = KEEPALIVE()

        for key, val in kwargs.items():
            setattr(self, key, val)

        self._args = list(args)

        # also sets the argument names to attributes,
        # so that we can do things like: op.T2 etc.
        names = cls.__dict__['_arg_names']
        assert len(args) == len(names)
        for i in range(len(names)):
            setattr(self, names[i], args[i])
        try:
            if cls.__dict__['_fnc_rtntype'](args) == int1_t:
                self.result.mu_type = int1_t
        except Exception:
            pass

    def __str__(self):
        cls = self.__class__
        rhs = "%s %s" % (self.opname, cls.__dict__['_fnc_str'](self))
        if self.result.mu_type is void_t:
            return rhs
        return "%s = %s" % (self.result.mu_name, rhs)

    def __repr__(self):
        return str(self)


def _newop(opname, arg_names, rtn_t_fnc, str_fnc):
    """
    Dynamically build an operation class
    :param opname: name of the operation
    :param arg_names: a string separated by ' ' denoting the name for the arguments
    :param rtn_t_fnc: function that computes the return type
    :param str_fnc: function that generates Mu code
    :return: created class instance
    """

    return type(opname, (MuOperation,),
                {'__init__': MuOperation.__init__,
                 '_fnc_rtntype': rtn_t_fnc,
                 '_fnc_str': str_fnc,
                 '_arg_names': arg_names.split(' ') if arg_names else []})


# ----------------------------------------------------------------
# Binary Operations
BINOPS = "ADD SUB MUL SDIV SREM UDIV UREM SHL LSHR ASHR AND OR XOR FADD FSUB FMUL FDIV FREM".split(' ')
for opname in BINOPS:
    globals()[opname] = _newop(opname, "op1 op2",
                               lambda (op1, op2): op1.mu_type,
                               lambda op: "<%s> %s %s %s" % (op.op1.mu_type.mu_name,
                                                             op.op1.mu_name if hasattr(op.op1, 'mu_name') else op.op1,
                                                             op.op2.mu_name if hasattr(op.op2, 'mu_name') else op.op2,
                                                             op.exc))


# ----------------------------------------------------------------
# Compare Operations
CMPOPS = ("EQ NE SGE SGT SLE SLT UGE UGT ULE ULT "
    "FFALSE FTRUE FUNO FUEQ FUNE FUGT FUGE FULT FULE "
    "FORD FOEQ FONE FOGT FOGE FOLT FOLE").split(' ')
for opname in CMPOPS:
    globals()[opname] = _newop(opname, "op1 op2",
                               lambda args: int1_t,
                               lambda op: "<%s> %s %s" % (op.op1.mu_type.mu_name,
                                                          op.op1.mu_name if hasattr(op.op1, 'mu_name') else op.op1,
                                                          op.op2.mu_name if hasattr(op.op2, 'mu_name') else op.op2,))


# ----------------------------------------------------------------
# Conversion Operations
# args: (opnd, T2)
CONVOPS = "TRUNC ZEXT SEXT FPTRUNC FPEXT FPTOUI FPTOSI UITOFP SITOFP BITCAST REFCAST PTRCAST".split(' ')
for opname in CONVOPS:
    globals()[opname] = _newop(opname, "opnd T2",
                               lambda (opnd, T2): T2,
                               lambda op: "<%s %s> %s" % (op.opnd.mu_type.mu_name, op.T2.mu_name, op.opnd.mu_name))


# ----------------------------------------------------------------
# args: (cond, ifTrue, ifFalse)
SELECT = _newop("SELECT", "cond ifTrue ifFalse",
                lambda (cond, ifT, ifF): ifT.mu_type,
                lambda op: "<%s %s> %s %s %s" % (op.cond.mu_type.mu_name,
                                                 op.result.mu_type.mu_name,
                                                 op.cond.mu_name,
                                                 op.ifTrue.mu_name,
                                                 op.ifFalse.mu_name))


# ----------------------------------------------------------------
# Intra-function Control Flow
BRANCH = _newop("BRANCH", "dest",
                lambda args: void_t,
                lambda op: "%s" % op.dest)

BRANCH2 = _newop("BRANCH2", "cond ifTrue ifFalse",
                 lambda args: void_t,
                 lambda op: "%s %s %s" % (op.cond.mu_name, op.ifTrue, op.ifFalse))

SWITCH = _newop("SWITCH", "opnd default cases",
                lambda args: void_t,
                lambda op: "<%s> %s %s { %s }" % (op.opnd.mu_type.mu_name, op.opnd.mu_name,
                                                  op.default,
                                                  ' '.join(["%s %s" % (v.mu_name, dst) for (v, dst) in op.cases])))


# ----------------------------------------------------------------
# Inter-function Control Flow
CALL = _newop("CALL", "callee args",
              lambda (callee, args): callee.mu_type.Sig.RTNS[0],
              lambda op: "<%s> %s (%s) %s %s" % (op.callee.mu_type.Sig.mu_name,
                                                 op.callee.mu_name,
                                                 ' '.join([str(arg.mu_name) for arg in op.args]),
                                                 op.exc, op.ka))

TAILCALL = _newop("TAILCALL", "callee args",
                  lambda args: void_t,
                  lambda op: "<%s> (%s) %s %s" % (op.callee.mu_type.Sig.mu_name,
                                                     ' '.join([str(arg.mu_name) for arg in op.args]),
                                                     op.exc, op.ka))

RET = _newop("RET", "rv",
             lambda args: void_t,
             lambda op: "(%s)" % (op.rv.mu_name if op.rv else ''))

THROW = _newop("THROW", "excobj",
               lambda args: void_t,
               lambda op: "%s" % op.excobj.mu_name)


# ----------------------------------------------------------------
# Aggregate Type Operations
EXTRACTVALUE = _newop("EXTRACTVALUE", "opnd idx",
                      lambda (opnd, idx): opnd.mu_type[idx],
                      lambda op: "<%s %d> %s" % (op.opnd.mu_type.mu_name, op.idx, op.opnd.mu_name))

INSERTVALUE = _newop("INSERTVALUE", "opnd idx val",
                     lambda (opnd, idx, val): opnd.mu_type,
                     lambda op: "<%s %d> %s %s" % (op.opnd.mu_type.mu_name, op.idx, op.opnd.mu_name, op.val.mu_name))

EXTRACTELEMENT = _newop("EXTRACTELEMENT", "opnd idx",
                        lambda (opnd, idx): opnd.mu_type.OF,
                        lambda op: "<%s %s> %s %s" % (op.opnd.mu_type, op.idx.mu_type, op.opnd.mu_name, op.idx.mu_name))

INSERTELEMENT = _newop("EXTRACTELEMENT", "opnd idx val",
                       lambda (opnd, idx, val): opnd.mu_type,
                       lambda op: "<%s %s> %s %s %s " % (op.opnd.mu_type, op.idx.mu_type,
                                                         op.opnd.mu_name, op.idx.mu_name, op.val.mu_name))


# ----------------------------------------------------------------
# Memory Operations
NEW = _newop("NEW", "T", lambda (T, ): MuRef(T), lambda op: "<%s> %s" % (op.T.mu_name, op.exc))
ALLOCA = _newop("ALLOCA", "T", lambda (T, ): MuIRef(T), NEW.__dict__['_fnc_str'])
NEWHYBRID = _newop("NEWHYBRID", "T length",
                   lambda (T, length): MuRef(T),
                   lambda op: "<%s %s> %s %s" % (op.T.mu_name, op.length.mu_type.mu_name,
                                                 op.length.mu_name, op.exc))
ALLOCAHYBRID = _newop("NEWHYBRID", "T length", lambda (T, length): MuRef(T), NEWHYBRID.__dict__['_fnc_str'])

GETIREF = _newop("GETIREF", "opnd",
                 lambda (opnd, ): MuIRef(opnd.mu_type.TO),
                 lambda op: "<%s> %s" % (op.opnd.mu_type.mu_name, op.opnd.mu_name))

GETFIELDIREF = _newop("GETFIELDIREF", "opnd idx",
                      lambda (opnd, idx): opnd.mu_type.__class__(opnd.mu_type.TO[idx]),
                      lambda op: "%s <%s %d> %s" % ("PTR" if isinstance(op.opnd.mu_type, MuUPtr) else "",
                                                    op.opnd.mu_type.TO.mu_name, op.idx, op.opnd.mu_name))

GETELEMIREF = _newop("GETELEMIREF", "opnd idx",
                     lambda (opnd, idx): opnd.mu_type.__class__(opnd.mu_type.TO[idx]),
                     lambda op: "%s <%s %s> %s %s" % ("PTR" if isinstance(op.opnd.mu_type, MuUPtr) else "",
                                                   op.opnd.mu_type.TO.mu_name, op.idx.mu_type.mu_name,
                                                   op.opnd.mu_name, op.idx.mu_name))

SHIFTIREF = _newop("SHIFTIREF", "opnd offset",
                   lambda (opnd, offset): opnd.mu_type,
                   lambda op: "%s <%s %s> %s %s" % ("PTR" if isinstance(op.opnd.mu_type, MuUPtr) else "",
                                                    op.opnd.mu_type.TO.mu_name, op.offset.mu_type.mu_name,
                                                    op.opnd.mu_name, op.offset.mu_name))

GETVARPARTIREF = _newop("GETVARPARTIREF", "opnd",
                        lambda (opnd, ): opnd.mu_type.__class__(opnd.mu_type.TO[-1]),
                        lambda op: "%s <%s> %s" % ("PTR" if isinstance(op.opnd.mu_type, MuUPtr) else "",
                                                   op.opnd.mu_type.TO.mu_name, op.opnd.mu_name))


# ----------------------------------------------------------------
# Memory Accessing
# NOTE: memory order is not implemented.
LOAD = _newop("LOAD", "loc",
              lambda (loc, ): loc.mu_type.TO,
              lambda op: "%s <%s> %s %s" % ("PTR" if isinstance(op.loc.mu_type, MuUPtr) else "",
                                            op.result.mu_type.mu_name, op.loc.mu_name,
                                            op.exc if hasattr(op, 'exc') else ''))

STORE = _newop("STORE", "loc val",
               lambda (loc, val): void_t,
               lambda op: "%s <%s> %s %s %s" % ("PTR" if isinstance(op.loc.mu_type, MuUPtr) else "",
                                                op.val.mu_type.mu_name, op.loc.mu_name, op.val.mu_name,
                                                op.exc if hasattr(op, 'exc') else ''))


# ----------------------------------------------------------------
# NOTE: only 1 return type
TRAP = _newop("TRAP", "T",
              lambda (T, ): T,
              lambda op: "<%s> %s %s" % (op.T.mu_name, op.exc, op.ka))


# ----------------------------------------------------------------
CCALL = _newop("CCALL", "callee args",
               lambda (callee, args): callee.mu_type.Sig.RTNS[0],
               lambda op: "%s <%s %s> %s (%s) %s %s" % ("#DEFAULT",
                                                        op.callee.mu_type.mu_name,
                                                        op.callee.mu_type.Sig.mu_name,
                                                        op.callee.mu_name,
                                                        ' '.join([str(arg.mu_name) for arg in op.args]),
                                                        op.exc, op.ka))


# ----------------------------------------------------------------
def _newcomminst(inst_name, arg_names, rtn_t_fnc, str_fnc):
    return type("COMMINST", (MuOperation,),
                {'__init__': MuOperation.__init__,
                 '_inst_mu_name': MuName(inst_name),
                 '_fnc_rtntype': rtn_t_fnc,
                 '_fnc_str': lambda op: "%s %s" % (op.__class__.__dict__['_inst_mu_name'], str_fnc(op)),
                 '_arg_names': arg_names.split(' ') if arg_names else []})

THREAD_EXIT = _newcomminst("uvm.thread_exit", "", lambda args: void_t, lambda op: "")

# Object pinning
NATIVE_PIN = _newcomminst("uvm.native.pin", "opnd",
                          lambda (opnd, ): MuUPtr(opnd.mu_type.TO),
                          lambda op: "<%s> (%s)" % (op.opnd.mu_type.mu_name, op.opnd.mu_name))
NATIVE_UNPIN = _newcomminst("uvm.native.unpin", "opnd",
                            lambda args: void_t,
                            lambda op: "<%s> (%s)" % (op.opnd.mu_type.mu_name, op.opnd.mu_name))

NATIVE_EXPOSE = _newcomminst("uvm.native.expose", "func cookie",
                             lambda (func, cookie): MuUFuncPtr(func.mu_type.Sig),
                             lambda op: "<[%s]> (%s, %s)" % (op.func.mu_type.Sig.mu_name,
                                                             op.func.mu_name, op.cookie.mu_name))

NATIVE_UNEXPOSE = _newcomminst("uvm.native.unexpose", "value",
                               lambda (value, ): void_t,
                               lambda op: "(%s)" % op.value.mu_name)

GET_THREADLOCAL = _newcomminst("uvm.get_threadlocal", "", lambda args: MuRef(void_t), lambda op: "")

SET_THREADLOCAL = _newcomminst("uvm.set_threadlocal", "ref", lambda args: void_t, lambda op: "(%s)" % op.ref)

# TODO: a few more?
