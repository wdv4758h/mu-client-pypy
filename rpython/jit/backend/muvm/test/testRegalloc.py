""" Tests for register allocation for common constructs
"""

import py
from rpython.jit.metainterp.history import (BasicFailDescr,
                                        BasicFinalDescr,
                                        JitCellToken,
                                        TargetToken)
from rpython.jit.metainterp.resoperation import rop
from rpython.jit.backend.llsupport.descr import GcCache
from rpython.jit.backend.detect_cpu import getcpuclass
from rpython.jit.backend.muvm.regalloc import Regalloc #, ARMFrameManager
from rpython.jit.backend.llsupport.regalloc import is_comparison_or_ovf_op
from rpython.jit.tool.oparser import parse
from rpython.rtyper.lltypesystem import lltype, llmemory
from rpython.rtyper.annlowlevel import llhelper
from rpython.rtyper.lltypesystem import rstr
from rpython.rtyper import rclass
from rpython.jit.codewriter.effectinfo import EffectInfo
from rpython.jit.codewriter import longlong
from rpython.jit.backend.llsupport.test.test_regalloc_integration import BaseTestRegalloc

### Specified from MuVM

rm = MuVMRegisterManager()

### Imported from arm. To be updated
### START: Unupdated (This will move as tests are updated for Mu)

def test_is_comparison_or_ovf_op():
    assert not is_comparison_or_ovf_op(rop.INT_ADD)
    assert is_comparison_or_ovf_op(rop.INT_ADD_OVF)
    assert is_comparison_or_ovf_op(rop.INT_EQ)

CPU = getcpuclass()

class MockGcDescr(GcCache):
    def get_funcptr_for_new(self):
        return 123
    get_funcptr_for_newarray = get_funcptr_for_new
    get_funcptr_for_newstr = get_funcptr_for_new
    get_funcptr_for_newunicode = get_funcptr_for_new

    def rewrite_assembler(self, cpu, operations):
        pass


class MockAssembler(object):
    gcrefs = None
    _float_constants = None

    def __init__(self, cpu=None, gc_ll_descr=None):
        self.movs = []
        self.performs = []
        self.lea = []
        if cpu is None:
            cpu = CPU(None, None)
            cpu.setup_once()
        self.cpu = cpu
        if gc_ll_descr is None:
            gc_ll_descr = MockGcDescr(False)
        self.cpu.gc_ll_descr = gc_ll_descr

    def dump(self, *args):
        pass

    def regalloc_mov(self, from_loc, to_loc):
        self.movs.append((from_loc, to_loc))

    def regalloc_perform(self, op, arglocs, resloc):
        self.performs.append((op, arglocs, resloc))

    def regalloc_perform_discard(self, op, arglocs):
        self.performs.append((op, arglocs))

    def load_effective_addr(self, *args):
        self.lea.append(args)


class RegAllocForTests(Regalloc):
    position = 0

    def _compute_next_usage(self, v, _):
        return -1


def get_zero_division_error(self):
    # for tests, a random emulated ll_inst will do
    ll_inst = lltype.malloc(rclass.OBJECT)
    ll_inst.typeptr = lltype.malloc(rclass.OBJECT_VTABLE,
                                    immortal=True)
    _zer_error_vtable = llmemory.cast_ptr_to_adr(ll_inst.typeptr)
    zer_vtable = self.cast_adr_to_int(_zer_error_vtable)
    zer_inst = lltype.cast_opaque_ptr(llmemory.GCREF, ll_inst)
    return zer_vtable, zer_inst

