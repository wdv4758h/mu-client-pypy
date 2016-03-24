"""
Defines the Mu instruction set
"""
from rpython.flowspace.model import Block, Variable
from rpython.mutyper.muts.muentity import MuName


# ----------------------------------------------------------------
# Clauses
class DEST:
    def __init__(self, blk, args):
        self.blk = blk
        self.args = args

    def __str__(self):
        return "%s(%s)" % (self.blk.mu_name, ' '.join([str(arg.mu_name) for arg in self.args]))


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
    def __init__(self, args, result=None, exc=EXCEPT(), ka=KEEPALIVE()):
        self.args = args
        if result:
            self.result = result
        else:
            self.result = Variable('rtn')
            cls = self.__class__
            self.result.mu_type = cls.__dict__['_fnc_rtntype'](args)
            self.result.mu_name = MuName(self.result.name, args[0].mu_name.scope)
        self.exc = exc
        self.ka = ka
        
    def __str__(self):
        cls = self.__class__
        return cls.__dict__['_fnc_str'](self)

    def __repr__(self):
        return str(self)


def _newop(opname, rtn_t_fnc, str_fnc):
    """
    Dynamically build an operation class
    :param opname: name of the operation
    :param rtn_t_fnc: function that computes the return type
    :param str_fnc: function that generates Mu code
    :return: created class instance
    """

    return type(opname, (MuOperation,),
                {'__init__': MuOperation.__init__,
                 '_fnc_rtntype': rtn_t_fnc,
                 '_fnc_str': str_fnc})


# ----------------------------------------------------------------
# Binary Operations
for opname in "ADD SUB MUL SDIV SREM UDIV UREM SHL LSHR ASHR AND OR XOR FADD FSUB FMUL FDIV FREM".split(' '):
    globals()[opname] = _newop(opname,
                               lambda args: args[0].mu_type,
                               lambda op: "%s = %s <%s> %s %s %s" % (op.result.mu_name,
                                                                     op.__class__.__name__,
                                                                     op.args[0].mu_type.mu_name,
                                                                     op.args[0].mu_name, op.args[1].mu_name,
                                                                     op.exc))
