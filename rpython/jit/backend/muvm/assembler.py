from rpython.jit.backend.muvm.opassembler import OpAssembler
from rpython.jit.backend.llsupport.assembler import BaseAssembler
from rpython.rlib.rmu import Mu


class AssemblerMu(OpAssembler, BaseAssembler):
    def __init__(self, cpu, translate_support_code=False):
        BaseAssembler.__init__(self, cpu, translate_support_code)
        muvm = Mu()
        mc = muvm.new_context()
        bndl = mc.new_bundle()
        vars = dict()
        type_int = mc.new_type_int(bndl, 32)
        type_int_64 = mc.new_type_int(bndl, 64)
        type_float = mc.new_type_float(bndl)
        #temporary constant declarations
        const_int_0 = mc.new_const_int(bndl, type_int, 0)
        const_float_0 = mc.new_const_float(bndl, type_float, 0.0)
        const_int_neg = mc.new_const_int(bndl, type_int, -1)

        sig = mc.new_funcsig(bndl, [], [])
        func = mc.new_func(bndl, sig)
        fv = mc.new_func_ver(bndl, func)
        bb = mc.new_bb(fv)

    def setup(self, looptoken):
        BaseAssembler.setup(self, looptoken)

    def assemble_bridge(self, faildescr, inputargs, operations,
                        original_loop_token, log, logger):
        # TODO
        pass