"""
Converts the LLTS types and operations to MuTS.
"""
from rpython.flowspace.model import FunctionGraph, Block, Link, Variable, Constant
from .muts.muentity import *
from rpython.rtyper.lltypesystem import lltype as llt
from .muts import mutype as mut
from .muts import muops as muop
from .ll2mu import *
import py
from rpython.tool.ansi_print import ansi_log


log = py.log.Producer("MuTyper")
py.log.setconsumer("MuTyper", ansi_log)


class MuTyper:
    def __init__(self):
        self.ldgcells = {}      # MuGlobalCells that need to be LOADed.
        self.gblcnsts = set()   # Constants that need to be defined on the global level
        pass

    def specialise(self, g):
        g.mu_name = MuName(g.name)
        g.mu_type = mut.MuFuncRef(mut.MuFuncSig([ll2mu_ty(arg.concretetype) for arg in g.startblock.inputargs],
                                                [ll2mu_ty(g.returnblock.inputargs[0].concretetype)]))
        for blk in g.iterblocks():
            self.specialise_block(blk)

        blk = self.proc_gcells()
        if blk:
            blk.inputargs = g.startblock.inputargs
            blk.exits = (Link([], g.startblock), )
            g.startblock = blk

        for idx, blk in enumerate(g.iterblocks()):
            blk.mu_name = MuName("blk%d" % idx, g)

    def specialise_block(self, blk):
        muops = []
        self.proc_arglist(blk.inputargs, blk)

        for op in blk.operations:
            # set up -- process the result and the arguments
            self.proc_arglist(op.args, blk)
            op.result = self.proc_arg(op.result, blk)
            op.result.mu_name = MuName(op.result.name, blk)
            try:
                muops += ll2mu_op(op)
            except NotImplementedError:
                log.warning("Ignoring '%s'." % op)
                muops += [op]
        blk.operations = tuple(muops)

    def proc_arglist(self, args, blk):
        for i in range(len(args)):
            args[i] = self.proc_arg(args[i], blk)

    def proc_arg(self, arg, blk):
        arg.mu_type = ll2mu_ty(arg.concretetype)
        if isinstance(arg, Constant):
            if isinstance(arg.mu_type, mut.MuRef):
                gcell = MuGlobalCell(arg.mu_type)
                gcell.value = ll2mu_val(arg.value)

                # A loaded gcell variable, ie. ldgcell = LOAD gcell
                ldgcell = Variable('ld' + gcell.mu_name._name)
                self.ldgcells[gcell] = ldgcell
                return ldgcell
            elif isinstance(arg.value, llt.LowLevelType):
                arg.value = ll2mu_ty(arg.value)
            elif not isinstance(arg.value, str):
                arg.value = ll2mu_val(arg.value, arg.concretetype)
        else:
            arg.mu_name = MuName(arg.name, blk)

        return arg

    def proc_gcells(self):
        if self.ldgcells:
            ops = []
            for gcell, ldgcell in self.ldgcells.items():
                ops.append(muop.LOAD(gcell, result=ldgcell))
            blk = Block([])
            blk.operations = tuple(ops)
            return blk
