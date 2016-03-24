"""
Defines the Mu instruction set
"""
from rpython.flowspace.model import Block, Variable


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
    def __init__(self, name, strfnc):
        self.opname = name
        self.strfnc = strfnc
    
    def __call__(self, args, result=None, exc=EXCEPT(), ka=KEEPALIVE()):
        self.args = args
        self.result = result if result else Variable('rtn')
        self.exc = exc
        self.ka = ka
        
    def __str__(self):
        return self.strfnc()

    def __repr__(self):
        return str(self)


# ----------------------------------------------------------------
# Binary Operations
_binop_strfnc = lambda op: "%s = %s <%s> %s %s %s" % (op.result, op.opname, op.args[0].mu_type,
                                          op.args[0], op.args[1], op.exc)

ADD = MuOperation("ADD", _binop_strfnc)
# TODO: the rest of the definitions
