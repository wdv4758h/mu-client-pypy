"""
Converts the LLTS types and operations to MuTS.
"""
from rpython.flowspace.model import FunctionGraph, Block, Link, Variable, Constant, c_last_exception, SpaceOperation
from rpython.mutyper.muts.muni import MuExternalFunc
from rpython.mutyper.muts.muops import DEST
from rpython.translator.mu.preps import prepare
from .muts.muentity import *
from rpython.rtyper.lltypesystem import lltype as llt
from rpython.rtyper.annlowlevel import MixLevelHelperAnnotator
from rpython.rtyper.llannotation import lltype_to_annotation as l2a
from rpython.translator.backendopt.all import backend_optimizations
from .muts import mutype as mut
from .muts import muops as muop
from .ll2mu import *
from .ll2mu import _MuOpList, _newprimconst
from .tools.textgraph import print_graph

import py
from rpython.tool.ansi_print import AnsiLogger


log = AnsiLogger("MuTyper")


class _NeedToLoadParentError(Exception):
    def __init__(self, cnst):
        self.cnst = cnst

    @staticmethod
    def need(cnst):
        if isinstance(cnst, Constant) and isinstance(cnst.value, lltype._ptr):
            ptr = cnst.value
            obj = ptr._obj
            wrprnt = getattr(obj, '_wrparent', None)
            if wrprnt:
                assert isinstance(obj, lltype._struct)
                prnt = wrprnt()
                ty = prnt._TYPE
                return len(ty._names) > 1
        return False


class MuTyper:
    def __init__(self, translator):
        self.ldgcells = {}      # MuGlobalCells that need to be LOADed.
        self._cnst_gcell_dict = {}  # mapping Constant to MuGlobalCell
        self._seen = set()
        self.externfncs = set()
        self._alias = {}
        self.tlr = translator
        self.mlha = MixLevelHelperAnnotator(self.tlr.rtyper)
        self.graphs = list(translator.graphs)
        self.helper_graphs = {}
        self._fncname_cntr_dic = {}

    def prepare_all(self):
        # wrapper outside of preps.prepare to provide for the name_dict
        self.graphs = self._prepare(self.graphs, self.tlr.entry_point_graph)

    def _prepare(self, graphs, entry_point):
        return prepare(graphs, entry_point, self._fncname_cntr_dic)

    def specialise_all(self):
        for g in self.graphs:
            print_graph(g)
            self.specialise(g)

        for g in self.helper_graphs.values():
            print_graph(g)
            self.specialise(g)

        self.tlr.graphs = self.graphs = self.graphs + self.helper_graphs.values()

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

        for blk in g.iterblocks():
            self.specialise_block(blk)

        self.proc_gcells()

    def specialise_block(self, blk):
        muops = _MuOpList()
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
                if not (len(muops) > 0 and muops[-1].opname == 'THROW'):
                    muops.append(muop.RET(blk.inputargs[0] if len(blk.inputargs) == 1 else None))
            elif len(blk.exits) == 1:
                muops.append(muop.BRANCH(DEST.from_link(blk.exits[0])))
            elif len(blk.exits) == 2:
                blk.exitswitch = self.proc_arg(blk.exitswitch, blk)
                if blk.exitswitch.mu_type is mutype.bool_t:
                    blk.exitswitch = muops.append(muop.EQ(blk.exitswitch, _newprimconst(mutype.bool_t, 1)))
                muops.append(muop.BRANCH2(blk.exitswitch, DEST.from_link(blk.exits[1]), DEST.from_link(blk.exits[0])))
            else:   # more than 2 exits -> use SWITCH statement
                blk.exitswitch = self.proc_arg(blk.exitswitch, blk)
                solid_exits = filter(lambda e: e.exitcase != 'default', blk.exits)
                exitcases = [Constant(e.llexitcase, lltype.typeOf(e.llexitcase)) for e in solid_exits]
                self.proc_arglist(exitcases, blk)
                cases = zip(exitcases, map(DEST.from_link, solid_exits))
                defl_exit = next((DEST.from_link(e) for e in blk.exits if e.exitcase == 'default'), cases[-1])
                muops.append(muop.SWITCH(blk.exitswitch, defl_exit, cases))

        else:
            muops[-1].exc = muop.EXCEPT(DEST.from_link(blk.exits[0]), DEST.from_link(blk.exits[1]))
        blk.operations = tuple(muops)

    def specialise_op(self, op, blk):
        muops = []

        # set up -- process the result and the arguments
        try:
            self.proc_arglist(op.args, blk)
        except _NeedToLoadParentError as e:
            # effectively insert a 'getfield' operation to get the field from parent structure.
            prnt = e.cnst.value._obj._wrparent()
            idx = e.cnst.value._obj._parent_index
            ty = e.cnst.value._obj._parent_type
            cnst_prnt = Constant(prnt, ty)
            _op = SpaceOperation('getfield', [cnst_prnt, Constant(idx, lltype.Void)], Variable())
            # replace the constant with the result of getfield
            op.args[op.args.index(e.cnst)] = _op.result
            # specialise the getfield operation
            muops += self.specialise_op(_op, blk)
            # try process the arguments again.
            self.proc_arglist(op.args, blk)

        op.result = self.proc_arg(op.result, blk)

        # translate operation
        try:
            _muops, res = ll2mu_op(op)
            if len(_muops) == 0:
                self._alias[op.result] = res     # no op -> result = args[0]

            # some post processing
            for _o in _muops:
                for i in range(len(_o._args)):
                    arg = _o._args[i]
                    if isinstance(arg, MuExternalFunc):
                        # Addresses of some C functions stored in global cells need to be processed.
                        self.externfncs.add(arg)
                    if isinstance(arg, mutype._mufuncref) and hasattr(arg, '_llhelper'):
                        # Some added LL helper functions need to be annotated and rtyped.
                        fnr = arg
                        llfnc = fnr._llhelper
                        graph = self.mlha.getgraph(llfnc, map(l2a, [a.concretetype for a in _o.args]),
                                                   l2a(_o.result.concretetype))
                        if not hasattr(fnr, 'graph'):
                            fnr.graph = graph
                        self.mlha.finish()
                        if hasattr(arg, '_postproc_fnc'):   # post-RTyper process (hack) the graph.
                            fnc = arg._postproc_fnc
                            fnc(graph)
                        backend_optimizations(self.tlr, [graph])
                        key = (graph.name, ) + tuple(a.concretetype for a in graph.startblock.inputargs)
                        if key not in self.helper_graphs:
                            graph = prepare([graph], graph)[0]
                            self.helper_graphs[key] = graph
                        else:
                            graph = self.helper_graphs[key]
                        _o.callee = graph
                if hasattr(_o.result, 'mu_name'):
                    _o.result.mu_name.scope = blk   # Correct the scope of result variables

            muops += _muops
        except NotImplementedError:
            log.warning("Ignoring '%s'." % op)
            self._alias[op.result] = op.args[0]

        return muops

    def proc_arglist(self, args, blk):
        for i in range(len(args)):
            args[i] = self.proc_arg(args[i], blk)

    def proc_arg(self, arg, blk):
        if arg in self._alias:
            return self._alias[arg]

        # replace the constant with the normalised container
        if isinstance(arg, Constant) and isinstance(arg.value, lltype._ptr) and isinstance(arg.value._obj, lltype._parentable):
            new_ptr = arg.value._obj._normalizedcontainer()._as_ptr()
            arg = Constant(new_ptr, new_ptr._TYPE)

        if _NeedToLoadParentError.need(arg):
            raise _NeedToLoadParentError(arg)
        if not hasattr(arg, 'mu_type'):     # has not been processed.
            arg.mu_type = ll2mu_ty(arg.concretetype)
            if isinstance(arg, Constant):
                if isinstance(arg.mu_type, mut.MuRef) and arg.value._obj is not None:
                    if arg not in self._cnst_gcell_dict:
                        gcell = MuGlobalCell(arg.mu_type, ll2mu_val(arg.value))
                        self._cnst_gcell_dict[arg] = gcell
                    else:
                        gcell = self._cnst_gcell_dict[arg]

                    return self._get_ldgcell_var(gcell, blk)
                else:
                    try:
                        arg.value = ll2mu_val(arg.value)
                        # Correcting type mismatch caused by incomplete type information when calling ll2mu_val.
                        if isinstance(arg.value, mutype._muprimitive) and arg.value._TYPE != arg.mu_type:
                            arg.value._TYPE = arg.mu_type
                        if not isinstance(arg.value, mutype._mufuncref):
                            arg.mu_name = MuName("%s_%s" % (str(arg.value), arg.mu_type.mu_name._name))
                    except (NotImplementedError, AssertionError, TypeError):
                        pass

            else:
                arg.mu_name = MuName(arg.name, blk)
        return arg

    def _get_ldgcell_var(self, gcell, blk):
        if gcell not in self.ldgcells:
            self.ldgcells[gcell] = {}
        try:
            return self.ldgcells[gcell][blk]
        except KeyError:
            # A loaded gcell variable, ie. ldgcell = LOAD gcell
            ldgcell = Variable('ld' + MuGlobalCell.prefix + gcell._T.mu_name._name)
            ldgcell.mu_type = gcell._T
            ldgcell.mu_name = MuName(ldgcell.name, blk)
            self.ldgcells[gcell][blk] = ldgcell
            return ldgcell

    def proc_gcells(self):
        for gcell, dic in self.ldgcells.items():
            for blk, ldgcell in dic.items():
                blk.operations = (muop.LOAD(gcell, result=ldgcell), ) + blk.operations
                del dic[blk]


