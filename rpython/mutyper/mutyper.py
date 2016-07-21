"""
Converts the LLTS types and operations to MuTS.
"""
from rpython.flowspace.model import Variable, Constant, c_last_exception
from rpython.mutyper.muts.muni import MuExternalFunc
from rpython.mutyper.muts.muops import DEST
from rpython.translator.mu.preps import prepare
from .muts.muentity import *
from rpython.rtyper.lltypesystem import lltype
from rpython.rtyper.annlowlevel import MixLevelHelperAnnotator
from rpython.rtyper.llannotation import lltype_to_annotation as l2a
from rpython.translator.backendopt.all import backend_optimizations
from .muts import mutype
from .muts import muops as muop
from . import ll2mu
from rpython.tool.ansi_mandelbrot import Driver

from rpython.tool.ansi_print import AnsiLogger


log = AnsiLogger("MuTyper")
mdb = Driver()


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

        # initialise thread local struct type
        if len(translator.annotator.bookkeeper.thread_local_fields) == 0:
            self.tlstt_t = mutype.MuStruct('mu_threadlocal', ('dummy', mutype.char_t))  # use a dummy struct when empty
        else:
            _tlflds = []
            for tlf in translator.annotator.bookkeeper.thread_local_fields:
                _tlflds.append((tlf.fieldname, ll2mu.ll2mu_ty(tlf.FIELDTYPE)))
            self.tlstt_t = mutype.MuStruct('mu_threadlocal', *_tlflds)
        setattr(ll2mu, '__mu_threadlocalstt_t', self.tlstt_t)

    def prepare_all(self):
        # wrapper outside of preps.prepare to provide for the name_dict
        self.graphs = self._prepare(self.graphs, self.tlr.entry_point_graph)

    def _prepare(self, graphs, entry_point):
        return prepare(graphs, entry_point, self._fncname_cntr_dic)

    def specialise_all(self):
        for g in self.graphs:
            self.specialise(g)

        for g in self.helper_graphs.values():
            self.specialise(g)

        self.tlr.graphs = self.graphs = self.graphs + self.helper_graphs.values()

        mdb.restart()
        ll2mu.resolve_refobjs()
        mdb.restart()

    def specialise(self, g):
        # log.info("specialising graph '%s'" % g.name)
        g.mu_name = MuName(g.name)
        get_arg_types = lambda lst: map(ll2mu.ll2mu_ty, map(lambda arg: arg.concretetype, lst))
        g.mu_type = mutype.MuFuncRef(mutype.MuFuncSig(get_arg_types(g.startblock.mu_inputargs),
                                                get_arg_types(g.returnblock.mu_inputargs)))
        ver = Variable('_ver')
        ver.mu_name = MuName(ver.name, g)
        g.mu_version = ver

        for idx, blk in enumerate(g.iterblocks()):
            blk.mu_name = MuName("blk%d" % idx, g)

        for blk in g.iterblocks():
            self.specialise_block(blk)

        self.proc_gcells()

        mdb.dot()

    def specialise_block(self, blk):
        muops = ll2mu._MuOpList()
        self.proc_arglist(blk.mu_inputargs, blk)
        if hasattr(blk, 'mu_excparam'):
            self.proc_arg(blk.mu_excparam, blk)

        for op in blk.operations:
            muops += self.specialise_op(op, blk)

        # Exits
        for e in blk.exits:
            self.proc_arglist(e.mu_args, blk)
        if blk.exitswitch is not c_last_exception:
            if len(blk.exits) == 0:
                if not (len(muops) > 0 and muops[-1].opname == 'THROW'):
                    muops.append(muop.RET(blk.mu_inputargs[0] if len(blk.mu_inputargs) == 1 else None))
            elif len(blk.exits) == 1:
                muops.append(muop.BRANCH(DEST.from_link(blk.exits[0])))
            elif len(blk.exits) == 2:
                blk.exitswitch = self.proc_arg(blk.exitswitch, blk)
                if blk.exitswitch.mu_type is mutype.bool_t:
                    blk.exitswitch = muops.append(muop.EQ(blk.exitswitch, ll2mu._newprimconst(mutype.bool_t, 1)))
                muops.append(muop.BRANCH2(blk.exitswitch, DEST.from_link(blk.exits[1]), DEST.from_link(blk.exits[0])))
            else:   # more than 2 exits -> use SWITCH statement
                blk.exitswitch = self.proc_arg(blk.exitswitch, blk)
                solid_exits = filter(lambda e: e.exitcase != 'default', blk.exits)
                exitcases = [Constant(e.llexitcase, lltype.typeOf(e.llexitcase)) for e in solid_exits]
                self.proc_arglist(exitcases, blk)
                cases = zip(exitcases, map(DEST.from_link, solid_exits))
                defl_exit = next((DEST.from_link(e) for e in blk.exits if e.exitcase == 'default'), cases[-1][1])
                muops.append(muop.SWITCH(blk.exitswitch, defl_exit, cases))

        else:
            muops[-1].exc = muop.EXCEPT(DEST.from_link(blk.exits[0]), DEST.from_link(blk.exits[1]))
        blk.mu_operations = tuple(muops)

    def specialise_op(self, op, blk):
        muops = []

        # set up -- process the result and the arguments
        self.proc_arglist(op.args, blk)
        op.result = self.proc_arg(op.result, blk)

        # translate operation
        try:
            _muops, res = ll2mu.ll2mu_op(op)
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
                if hasattr(_o, 'result') and hasattr(_o.result, 'mu_name'):
                    _o.result.mu_name.scope = blk   # Correct the scope of result variables

            muops += _muops
        except ll2mu.IgnoredLLOp:
            if len(op.args) == 1:
                self._alias[op.result] = op.args[0]

        return muops

    def proc_arglist(self, args, blk):
        for i in range(len(args)):
            args[i] = self.proc_arg(args[i], blk)

    def proc_arg(self, arg, blk):
        if arg in self._alias:
            return self._alias[arg]

        if isinstance(arg, Variable):
            if not (hasattr(arg, 'mu_type') and hasattr(arg, 'mu_name')):
                arg.mu_type = ll2mu.ll2mu_ty(arg.concretetype)
                arg.mu_name = MuName(arg.name, blk)

        elif isinstance(arg, Constant):
            llv = arg.value
            if arg.concretetype is lltype.Void:
                if isinstance(llv, mutype.MuType):
                    return arg
                elif isinstance(llv, lltype.LowLevelType):
                    Constant.__init__(arg, ll2mu.ll2mu_ty(llv), lltype.Void)
            else:
                if not hasattr(arg, 'mu_type'):  # has not been processed.
                    try:
                        muv = ll2mu.ll2mu_val(llv)
                        mut = ll2mu.ll2mu_ty(arg.concretetype)
                        if isinstance(muv, mutype._muprimitive) and muv._TYPE != mut:
                            # log.warning("correcting the type of '%(muv)s' from '%(type1)s' to '%(type2)s'." %
                            #             {'muv': muv, 'type1': muv._TYPE, 'type2': mut})
                            muv._TYPE = mut
                        # fix the type mismatch, all heap constants must be refs
                        if not isinstance(muv, mutype._munullref) and isinstance(muv._TYPE, mutype.MuUPtr):
                            muv._TYPE = mutype.MuRef(muv._TYPE.TO)
                            mut = muv._TYPE
                        Constant.__init__(arg, muv, arg.concretetype)
                        arg.mu_type = mut
                        if isinstance(muv, (mutype._muprimitive, mutype._munullref)):
                            arg.mu_name = MuName("%s_%s" % (str(arg.value), arg.mu_type.mu_name._name))
                    except ll2mu.IgnoredLLVal:
                        # log.warning("can not process '%(arg)s' in mutyper, ignored." % locals())
                        pass

                if isinstance(arg.value, mutype._muref):
                    if arg not in self._cnst_gcell_dict:
                        gcl = MuGlobalCell(arg.mu_type, arg.value)
                        self._cnst_gcell_dict[arg] = gcl
                    else:
                        gcl = self._cnst_gcell_dict[arg]
                    return self._get_ldgcell_var(gcl, blk)

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
                blk.mu_operations = (muop.LOAD(gcell, result=ldgcell), ) + blk.mu_operations
                del dic[blk]


