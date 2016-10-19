from rpython.jit.backend.muvm.arch import JITFRAME_FIXED_SIZE
from rpython.jit.backend.muvm.assembler import AssemblerMu
from rpython.jit.backend.muvm.registers import all_regs
from rpython.jit.backend.llsupport import jitframe
from rpython.jit.backend.llsupport.llmodel import AbstractLLCPU
from rpython.rlib.jit_hooks import LOOP_RUN_CONTAINER
from rpython.rtyper.lltypesystem import lltype, llmemory

jitframe.STATICSIZE = JITFRAME_FIXED_SIZE


class MuCPU(AbstractLLCPU):
    IS_64_BIT = True

    supports_floats = True
    supports_longlong = True
    supports_singlefloats = True

    backend_name = 'Mu'

    # might need to initialize all_reg_indexes
    gen_regs = all_regs
    float_regs = all_regs

    def __init__(self, rtyper, stats, opts=None, translate_support_code=False,
                 gcdescr=None):
        AbstractLLCPU.__init__(self, rtyper, stats, opts,
                               translate_support_code, gcdescr)
        self.assembler = None

    def set_debug(self, flag):
        return self.assembler.set_debug(flag)

    def setup(self):
        self.assembler = AssemblerMu(self, self.translate_support_code)

    def setup_once(self):
        self.assembler.setup_once()

    def finish_once(self):
        self.assembler.finish_once()

    def compile_bridge(self, faildescr, inputargs, operations,
                       original_loop_token, log=True, logger=None):
        clt = original_loop_token.compiled_loop_token
        clt.compiling_a_bridge()
        return self.assembler.assemble_bridge(faildescr, inputargs,
                                              operations,
                                              original_loop_token, log, logger)

    def cast_ptr_to_int(x):
        adr = llmemory.cast_ptr_to_adr(x)
        return MuCPU.cast_adr_to_int(adr)

    cast_ptr_to_int._annspecialcase_ = 'specialize:arglltype(0)'
    cast_ptr_to_int = staticmethod(cast_ptr_to_int)

    def redirect_call_assembler(self, oldlooptoken, newlooptoken):
        self.assembler.redirect_call_assembler(oldlooptoken, newlooptoken)

    def invalidate_loop(self, looptoken):
        """Activate all GUARD_NOT_INVALIDATED in the loop and its attached
        bridges.  Before this call, all GUARD_NOT_INVALIDATED do nothing;
        after this call, they all fail.  Note that afterwards, if one such
        guard fails often enough, it has a bridge attached to it; it is
        possible then to re-call invalidate_loop() on the same looptoken,
        which must invalidate all newer GUARD_NOT_INVALIDATED, but not the
        old one that already has a bridge attached to it."""

        for jmp, tgt in looptoken.compiled_loop_token.invalidate_positions:
            # TODO: depends on how guards are implemented
            pass
        # positions invalidated
        looptoken.compiled_loop_token.invalidate_positions = []

    def get_all_loop_runs(self):
        # not implemented
        return lltype.malloc(LOOP_RUN_CONTAINER, 0)

    def build_regalloc(self):
        ''' for tests'''
        from rpython.jit.backend.muvm.regalloc import Regalloc
        assert self.assembler is not None
        return Regalloc(self.assembler)