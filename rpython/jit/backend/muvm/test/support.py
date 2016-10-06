from rpython.jit.backend.detect_cpu import getcpuclass, MU_VM
from rpython.jit.metainterp.test import support
from rpython.rtyper.lltypesystem import lltype
from rpython.rtyper.lltypesystem import rffi


class JitMuMixin(support.LLJitMixin):
    type_system = 'lltype'
    CPUClass = getcpuclass(MU_VM)
    basic = False

def run_asm(asm):
    # TODO: coppied from ARM, does it need changes?
    BOOTSTRAP_TP = lltype.FuncType([], lltype.Signed)
    addr = asm.mc.materialize(asm.cpu, [], None)
    assert addr % 8 == 0
    func = rffi.cast(lltype.Ptr(BOOTSTRAP_TP), addr)
    asm.mc._dump_trace(addr, 'test.mu')
    return func()