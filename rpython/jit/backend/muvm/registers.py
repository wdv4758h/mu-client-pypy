""" Modified version of ../arm/registers.py. Will update as needed.
"""
from rpython.jit.backend.muvm.locations import VFPSSA
from rpython.jit.backend.muvm.locations import SVFPSSA
from rpython.jit.backend.muvm.locations import SSA
from rpython.jit.metainterp.history import (Const, ConstInt, ConstFloat,
                                            ConstPtr,
                                            INT, REF, FLOAT)

registers = []      # Holds SSA vars
vfpregisters = []   # Only using registers for now
svfpregisters = []  # Currently unused


all_regs = []
all_vfp_regs = vfpregisters

argument_regs = caller_resp = []
callee_resp = []
callee_saved_registers = callee_resp 
callee_restored_registers = callee_resp

vfp_argument_regs = caller_vfp_resp = []
svfp_argument_regs = []
callee_vfp_resp = []

callee_saved_vfp_registers = callee_vfp_resp

