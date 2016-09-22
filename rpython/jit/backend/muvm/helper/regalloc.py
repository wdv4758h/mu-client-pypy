from rpython.jit.backend.muvm import conditions as c
from rpython.jit.backend.muvm import registers as r
from rpython.jit.metainterp.history import Const, ConstInt, FLOAT
from rpython.rlib.objectmodel import we_are_translated

VMEM_imm_size=0x3FC
default_imm_size=0xFF

# Check that prepare_binop_int is defined properly. Namely, that `self' will
# work properly. 
def _prepare_binop_int(self, op, fcond):
    #TODO: check_imm_box - looks for ConstInt. Is this right?
    boxes = op.getarglist()
    a0, a1 = boxes
    imm_a0 = check_imm_box(a0)
    imm_a1 = check_imm_box(a1)
    if not imm_a0 and imm_a1:
        l0 = self.make_sure_var_in_reg(a0, boxes)
        l1 = self.convert_to_imm(a1)
    elif imm_a0 and not imm_a1:
        l0 = self.convert_to_imm(a0)
        l1 = self.make_sure_var_in_reg(a1, boxes)
    else:
        l0 = self.make_sure_var_in_reg(a0, boxes)
        l1 = self.make_sure_var_in_reg(a1, boxes)
    return [l0, l1]

def prepare_binop_int(self, op, fcond):
    locs = self._prepare_binop_int(op, fcond)
    self.possibly_free_vars_for_op(op)
    self.free_temp_vars()
    res = self.force_allocate_reg(op)
    return locs + [res]

def check_imm_arg(arg, size=default_imm_size, allow_zero=True):
    #NOTE: Always false
    return False

def check_imm_box(arg, size=0xFF, allow_zero=True):
    #NOTE: I'm guessing always false
    return False

def prepare_op_ri(name=None, imm_size=0xFF, commutative=True, allow_zero=True):
    #TODO
    def f(self, op, fcond):
        assert fcond is not None
        a0 = op.getarg(0)
        a1 = op.getarg(1)
        boxes = list(op.getarglist())
        imm_a0 = check_imm_box(a0, imm_size, allow_zero=allow_zero)
        imm_a1 = check_imm_box(a1, imm_size, allow_zero=allow_zero)
        if not imm_a0 and imm_a1:
            l0 = self.make_sure_var_in_reg(a0)
            l1 = self.convert_to_imm(a1)
        elif commutative and imm_a0 and not imm_a1:
            l1 = self.convert_to_imm(a0)
            l0 = self.make_sure_var_in_reg(a1, boxes)
        else:
            # This should ALWAYS run for now
            # Get rid of make_sure_var_in_reg OR override definition
            l0 = self.make_sure_var_in_reg(a0, boxes)
            l1 = self.make_sure_var_in_reg(a1, boxes)
        self.possibly_free_vars_for_op(op)
        self.free_temp_vars()
        res = self.force_allocate_reg(op, boxes)
        return [l0, l1, res]
    if name:
        f.__name__ = name
    return f

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

