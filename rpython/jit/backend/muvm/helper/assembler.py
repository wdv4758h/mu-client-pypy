import rpython.jit.backend.muvm.conditions as c
from rpython.rlib.rarithmetic import intmask
from rpython.jit.metainterp.history import FLOAT
from rpython.jit.metainterp.resoperation import rop
import rpython.jit.backend.muvm.registers as r
from rpython.rtyper.lltypesystem import rffi, lltype


def flush_cc(asm, condition, result_loc):
    #TODO
    pass


def do_emit_cmp_op(self, arglocs, condition, signed, fp):
    #TODO
    pass


def gen_emit_cmp_op(condition, signed=True, fp=False):
    #TODO
    pass

def count_reg_args(args):
    #TODO
    pass

class Saved_Volatiles(object):
    """ used in _gen_leave_jitted_hook_code to save volatile registers
        in ENCODING AREA around calls
    """

    def __init__(self, codebuilder, save_RES=True, save_FLOAT=True):
        pass

