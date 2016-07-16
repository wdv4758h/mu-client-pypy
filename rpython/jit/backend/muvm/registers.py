""" Modified version of ../muvm/registers.py. Will update as needed.
"""
#from rpython.jit.backend.arm.locations import VFPRegisterLocation
#from rpython.jit.backend.arm.locations import SVFPRegisterLocation
#from rpython.jit.backend.arm.locations import RegisterLocation
from rpython.jit.metainterp.history import (Const, ConstInt, ConstFloat,
                                            ConstPtr,
                                            INT, REF, FLOAT)

registers = []
vfpregisters = []
svfpregisters = []


all_regs = []
all_vfp_regs = vfpregisters[]

argument_regs = caller_resp = []
callee_resp = []
callee_saved_registers = callee_resp 
callee_restored_registers = callee_resp

vfp_argument_regs = caller_vfp_resp = []
svfp_argument_regs = []
callee_vfp_resp = []

callee_saved_vfp_registers = callee_vfp_resp

class Reg(object):
    """ Default register type. """
    type = None
    size = 0
    val  = None

class IntReg(Reg):
    type = INT
    def __init__(size = None, val = None):
        self.size = size
        self.val = val

class FPReg(Reg):
    type = FLOAT
    def __init__(size = None, val = None):
        assert size in (None, 32, 64)
        self.size = size
        self.val = val

