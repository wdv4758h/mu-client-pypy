"""
Converts the LLTS types and operations to MuTS.
"""
from rpython.flowspace.model import FunctionGraph, Block, Link, Variable, Constant, c_last_exception
from rpython.mutyper.muts.muni import MuExternalFunc
from rpython.mutyper.muts.muops import DEST
from .muts.muentity import *
from rpython.rtyper.lltypesystem import lltype as llt
from .muts import mutype as mut
from .muts import muops as muop
from .ll2mu import *
from .ll2mu import _MuOpList
from.adrderv import AddressDerivationTracker
import py
from rpython.tool.ansi_print import ansi_log


log = py.log.Producer("MuTyper")
py.log.setconsumer("MuTyper", ansi_log)


class MuTyper:
    def __init__(self):
        self.ldgcells = {}      # MuGlobalCells that need to be LOADed.
        self.gblcnsts = set()   # Constants that need to be defined on the global level
        self.gbltypes = set()   # Types that need to be defined on the global level
        self._cnst_gcell_dict = {}  # mapping Constant to MuGlobalCell
        self._seen = set()
        self._addrder = AddressDerivationTracker()
        self._externfncs = {}   # MuExternalFunc -> {FunctionGraph: [MuOperation]}
        pass

    def specialise(self, g):
        g.mu_name = MuName(g.name)
        get_arg_types = lambda lst: map(ll2mu_ty, map(lambda arg: arg.concretetype, lst))
        g.mu_type = mut.MuFuncRef(mut.MuFuncSig(get_arg_types(g.startblock.inputargs),
                                                get_arg_types(g.returnblock.inputargs)))
        ver = Variable('_ver')
        ver.mu_name = MuName(ver.name, g)
        g.mu_version = ver

        for idx, blk in enumerate(g.iterblocks()):
            blk.mu_name = MuName("blk%d" % idx, g)

        self._addrder.analyse(g)    # tag the Address types

        for blk in g.iterblocks():
            self.specialise_block(blk)

        self.proc_gcells(g)
        self.proc_externfuncs(g)

    def specialise_block(self, blk):
        muops = []
        self.proc_arglist(blk.inputargs, blk)
        if hasattr(blk, 'mu_excparam'):
            self.proc_arg(blk.mu_excparam, blk)

        for op in blk.operations:
            muops += self.specialise_op(op, blk)

        # Exits
        for e in blk.exits:
            self.proc_arglist(e.args, blk)
        if blk.exitswitch is not c_last_exception:
            if len(blk.exits) == 0:
                muops.append(muop.RET(blk.inputargs[0] if len(blk.inputargs) == 1 else None))
            elif len(blk.exits) == 1:
                muops.append(muop.BRANCH(DEST.from_link(blk.exits[0])))
            elif len(blk.exits) == 2:
                blk.exitswitch = self.proc_arg(blk.exitswitch, blk)
                muops.append(muop.BRANCH2(blk.exitswitch, DEST.from_link(blk.exits[0]), DEST.from_link(blk.exits[1])))
        blk.operations = tuple(muops)

    def specialise_op(self, op, blk):
        muops = []

        # set up -- process the result and the arguments
        self.proc_arglist(op.args, blk)
        op.result = self.proc_arg(op.result, blk)
        # op.result.mu_name = MuName(op.result.name, blk)

        # translate operation
        try:
            _muops = ll2mu_op(op)

            # some post processing
            for _o in _muops:
                for i in range(len(_o._args)):
                    arg = _o._args[i]
                    # picking out the generated (must be primitive) constants
                    if isinstance(arg, Constant):
                        assert isinstance(arg.mu_type, mutype.MuPrimitive)
                        self.gblcnsts.add(arg)
                    if isinstance(arg, MuExternalFunc):
                        # Addresses of some C functions stored in global cells need to be processed.
                        try:
                            d = self._externfncs[arg]
                        except KeyError:
                            d = {}
                        g = blk.mu_name.scope
                        try:
                            l = d[g]
                        except KeyError:
                            l = []
                        l.append(_o)
                        d[g] = l
                        self._externfncs[arg] = d
                        # needs more processing (LOAD, PTRCAST)
            muops += _muops
        except NotImplementedError:
            log.warning("Ignoring '%s'." % op)

        # process the potential exception clause
        exc = getattr(op, 'mu_exc', None)
        if exc:
            self.proc_arglist(exc.nor.args, blk)
            self.proc_arglist(exc.exc.args, blk)
            muops[-1].exc = exc

        return muops

    def proc_arglist(self, args, blk):
        for i in range(len(args)):
            args[i] = self.proc_arg(args[i], blk)

    def proc_arg(self, arg, blk):
        arg.mu_type = ll2mu_ty(arg.concretetype)
        self.gbltypes.add(arg.mu_type)
        if isinstance(arg, Constant):
            if isinstance(arg.mu_type, mut.MuRef):
                if arg not in self._cnst_gcell_dict:
                    gcell = MuGlobalCell(arg.mu_type, ll2mu_val(arg.value))
                    self._cnst_gcell_dict[arg] = gcell
                else:
                    gcell = self._cnst_gcell_dict[arg]

                return self._get_ldgcell_var(gcell, blk)
            elif isinstance(arg.value, llt.LowLevelType):
                arg.value = ll2mu_ty(arg.value)
            elif isinstance(arg.value, llmemory.CompositeOffset):
                pass    # ignore AddressOffsets; they will be dealt with in ll2mu_op.
            elif not isinstance(arg.value, (str, dict)):
                arg.value = ll2mu_val(arg.value)
                if not isinstance(arg.value, mutype._mufuncref):
                    self.gblcnsts.add(arg)
                    arg.mu_name = MuName(str(arg.value))
        else:
            arg.mu_name = MuName(arg.name, blk)
        return arg

    def _get_ldgcell_var(self, gcell, blk):
        if gcell not in self.ldgcells:
            self.ldgcells[gcell] = {}
        try:
            return self.ldgcells[gcell][blk.mu_name.scope]
        except KeyError:
            # A loaded gcell variable, ie. ldgcell = LOAD gcell
            ldgcell = Variable('ld' + MuGlobalCell.prefix + gcell._T.mu_name._name)
            ldgcell.mu_type = gcell._T
            ldgcell.mu_name = MuName(ldgcell.name, blk)
            self.ldgcells[gcell][blk.mu_name.scope] = ldgcell
            return ldgcell

    def proc_gcells(self, g):
        ops = []
        for gcell, dic in self.ldgcells.items():
            if g in dic:
                ldgcell = dic[g]
                ops.append(muop.LOAD(gcell, result=ldgcell))

        if len(ops) > 0:
            blk = Block([])
            blk.operations = tuple(ops)
            blk.mu_name = MuName("blk_load", g)
            blk.inputargs = g.startblock.inputargs
            blk.exits = (Link(g.startblock.inputargs, g.startblock),)
            blk.operations += (muop.BRANCH(DEST.from_link(blk.exits[0])),)
            g.startblock = blk

    def proc_externfuncs(self, g):
        blk_init = g.startblock
        ops = _MuOpList()
        for extfnc, dic in self._externfncs.items():
            if g in callsites:
                callsites = dic[g]
                adr = ops.append(muops.LOAD(extfnc.gcl_adr))
                ptr = ops.append(muops.PTRCAST(adr, extfnc))
                for ccall in callsites:
                    ccall.callee = ptr
                blk_init.operations += tuple(ops)
