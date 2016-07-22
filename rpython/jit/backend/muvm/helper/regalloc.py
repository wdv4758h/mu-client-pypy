from rpython.jit.backend.muvm import conditions as c
from rpython.jit.backend.muvm import registers as r
from rpython.jit.metainterp.history import Const, ConstInt, FLOAT
from rpython.rlib.objectmodel import we_are_translated

VMEM_imm_size=0x3FC
default_imm_size=0xFF

def check_imm_arg(arg, size=default_imm_size, allow_zero=True):
    #TODO
    pass

def check_imm_box(arg, size=0xFF, allow_zero=True):
    #TODO
    pass

def prepare_op_ri(name=None, imm_size=0xFF, commutative=True, allow_zero=True):
    #TODO
    pass

def prepare_unary_op(self, op, fcond):
    #TODO
    pass

def prepare_two_regs_op(self, op, fcond):
    #TODO
    pass

def prepare_float_cmp(self, op, fcond):
    #TODO
    pass

def prepare_op_by_helper_call(name):
    #TODO
    pass

def prepare_int_cmp(self, op, fcond):
    #TODO
    pass

def prepare_unary_cmp(self, op, fcond):
    #TODO
    pass

