from rpython.jit.backend.detect_cpu import getcpuclass, MU_VM
from rpython.jit.metainterp.test import support


class JitMuMixin(support.LLJitMixin):
    type_system = 'lltype'
    CPUClass = getcpuclass(MU_VM)
    basic = False
