from rpython.flowspace.model import Variable, Constant, c_last_exception
from rpython.rtyper.lltypesystem import lltype, llmemory
from rpython.translator.backendopt.removenoops import remove_unaryops
from rpython.translator.mu import mutype
from rpython.translator.mu.ll2mu import LL2MuMapper, varof
from rpython.rlib.objectmodel import CDefinedIntSymbolic
from rpython.tool.ansi_mandelbrot import Driver
from rpython.tool.ansi_print import AnsiLogger
log = AnsiLogger("MuTyper")
mdb = Driver()

class MuTyper:
    def __init__(self, tlc):
        # type: (rpython.translator.translator.TranslationContext) -> None
        self._graphname_cntr_dict = {}
        self.tlc = tlc
        self.ll2mu = LL2MuMapper(tlc.rtyper)
        self._objrefid2gcl_dic = {}

    def init_threadlocal_struct_type(self):
        # determine thread local struct type
        tlflds = self.tlc.annotator.bookkeeper.thread_local_fields
        if len(tlflds) == 0:
            # self.TLSTT = mutype.MuStruct('mu_tlstt', ('dummy', mutype.char_t))  # use a dummy struct when empty
            self.TLStt = mutype.MU_VOID
        else:
            _tlflds = []
            for tlf in tlflds:
                _tlflds.append((tlf.fieldname, self.ll2mu.map_type(tlf.FIELDTYPE)))
            self.TLStt = mutype.MuStruct('mu_tlstt', *_tlflds)
        self.ll2mu.set_threadlocal_struct_type(self.TLStt)

    def prepare_all(self):
        self.graphs = prepare(self.tlc.graphs, self.tlc.entry_point_graph)

    def specialise_all(self):
        if not hasattr(self, 'graphs'):
            raise AttributeError("don't have graphs. Run prepare_all() first.")

        self.graphs.add(self.ll2mu.ll_identityhash_c.value.graph)
        processed = []
        while len(self.graphs) > 0:
            g = self.graphs.pop()
            self.specialise_graph(g)
            processed.append(g)

        self.tlc.graphs = self.graphs = processed

    def specialise_graph(self, g):
        ret_llt = g.returnblock.inputargs[0].concretetype if len(g.returnblock.inputargs) == 1 else lltype.Void
        arg_llts = map(lambda arg: arg.concretetype, g.startblock.inputargs)
        g.sig = mutype.MuFuncSig([self.ll2mu.map_type(arg_t) for arg_t in arg_llts],
                                 [self.ll2mu.map_type(ret_llt)] if ret_llt != lltype.Void else [])
        for blk in g.iterblocks():
            self.specialise_block(blk)

        remove_unaryops(g, ['same_as', 'likely'])

    def specialise_block(self, blk):
        # specialise inputargs
        blk.inputargs = [self.specialise_arg(arg) for arg in blk.inputargs]

        # specialise operations
        muops = []
        for op in blk.operations:
            muops.extend(self.specialise_operation(op))

        # specialise exits
        ldgcell_ops = []
        for e in blk.exits:
            e.args = [self.specialise_arg(arg) for arg in e.args]
            ldgcell_ops.extend(self.extract_load_gcell(e.args))

        if blk.exitswitch is not c_last_exception:
            if len(blk.exits) == 0:
                if len(muops) == 0 or muops[-1].opname not in ("mu_throw", "mu_comminst"):
                    muops.append(self.ll2mu.gen_mu_ret(blk.inputargs[0] if len(blk.inputargs) == 1 else None))

            elif len(blk.exits) == 1:
                muops.append(self.ll2mu.gen_mu_branch(blk.exits[0]))

            elif len(blk.exits) == 2:
                blk.exitswitch = self.specialise_arg(blk.exitswitch)
                if not (blk.exitswitch.concretetype is mutype.MU_INT1):
                    MuT = blk.exitswitch.concretetype
                    flag = varof(mutype.MU_INT1)
                    muops.append(self.ll2mu.gen_mu_cmpop('EQ', blk.exitswitch,
                                                         Constant(MuT._val_type(1), MuT), flag))
                    blk.exitswitch = flag
                muops.append(self.ll2mu.gen_mu_branch2(blk.exitswitch, blk.exits[1], blk.exits[0]))

            else:  # more than 2 exits -> use SWITCH statement
                blk.exitswitch = self.specialise_arg(blk.exitswitch)
                cases = filter(lambda e: e.exitcase != 'default', blk.exits)
                for e in cases:
                    e.exitcase = self.specialise_arg(Constant(e.llexitcase, lltype.typeOf(e.llexitcase)))
                defl_exit = next((e for e in blk.exits if e.exitcase == 'default'), cases[-1])
                muops.append(self.ll2mu.gen_mu_switch(blk.exitswitch, defl_exit, cases))

        elif muops[-1].opname == 'mu_ccall':
            # NOTE: CCALL will NEVER throw a Mu exception.
            # still not sure why calling a native C library function will throw an RPython exception...
            # So in this case just branch the normal case
            muops.append(self.ll2mu.gen_mu_branch(blk.exits[0]))
        elif muops[-1].opname == 'mu_binop':    # binop overflow
            metainfo = muops[-1].args[-1].value
            statres_V = metainfo['status'][1][0]     # only V is used at this moment
            blk.exitswitch = statres_V
            muops.append(self.ll2mu.gen_mu_branch2(blk.exitswitch, blk.exits[1], blk.exits[0]))
        else:   # exceptional branching for mu_call, mu_comminst
            metainfo = muops[-1].args[-1].value
            metainfo['excclause'] = self.ll2mu.exc_clause(blk.exits[0], blk.exits[1])

        muops = muops[:-1] + ldgcell_ops + [muops[-1]]
        blk.operations = muops

    def specialise_arg(self, arg):
        if isinstance(arg.concretetype, lltype.LowLevelType):   # has not been processed
            LLT = arg.concretetype
            if isinstance(arg, Variable):
                arg.concretetype = self.ll2mu.map_type(LLT)
                self.ll2mu.resolve_ptr_types()
            elif isinstance(arg, Constant):
                llv = arg.value
                if LLT is lltype.Void:
                    if isinstance(arg.value, lltype.LowLevelType):  # a type constant
                        arg.__init__(self.ll2mu.map_type(llv), mutype.MU_VOID)
                        self.ll2mu.resolve_ptr_types()
                    else:   # for other non-translation constants, just keep the value
                        arg.__init__(llv, mutype.MU_VOID)
                else:
                    if isinstance(llv, CDefinedIntSymbolic) and llv.default == '?':
                        return arg  # ignore it; it should be dealt with when translating ops

                    MuT = self.ll2mu.map_type(LLT)
                    muv = self.ll2mu.map_value(llv)
                    self.ll2mu.resolve_ptr_types()
                    self.ll2mu.resolve_ptr_values()

                    if isinstance(muv, mutype._muufuncptr):
                        MuT = mutype.mutypeOf(muv)

                    assert mutype.mutypeOf(muv) == MuT

                    if isinstance(muv, mutype._muobject_reference):
                        GCl_T = mutype.MuGlobalCell(MuT)
                        if id(muv) in self._objrefid2gcl_dic:
                            gcl = self._objrefid2gcl_dic[id(muv)]
                        else:
                            gcl = mutype.new(GCl_T)
                            gcl._store(muv)
                            self._objrefid2gcl_dic[id(muv)] = gcl
                        arg.__init__(gcl, GCl_T)
                    else:
                        arg.__init__(muv, MuT)
        return arg

    def specialise_operation(self, llop):
        def skip(llop):
            return llop.opname in (
                "hint",
                "likely",
                "debug_flush",
                "debug_forked",
                "debug_offset",
                "debug_print",
                "debug_start",
                "debug_stop",
                "gc_add_memory_pressure",
                "gc_set_max_heap_size",
                "gc_thread_after_fork",
                "gc_writebarrier",
                "jit_conditional_call",
                "jit_force_quasi_immutable",
                "jit_force_virtual",
                "jit_is_virtual",
                "jit_marker",
            ) or (llop.opname.startswith('mu_') and llop.opname not in (
                'mu_getgcidhash',
                'mu_setgcidhash',
                'mu_thread_exit',
                'mu_threadlocalref_init',
            ))

        if llop.opname == 'force_cast':
            # HACK: save original arg and result types to discern signedness.
            llop._src_llt = llop.args[0].concretetype
            llop._res_llt = llop.result.concretetype

        llop.args = [self.specialise_arg(arg) for arg in llop.args]
        llop.result = self.specialise_arg(llop.result)

        if skip(llop):      # translate the concretetype regardless
            return [llop]

        muops = []
        muops.extend(self.extract_load_gcell(llop.args))
        muops.extend(self.ll2mu.map_op(llop))
        return muops

    def extract_load_gcell(self, args):
        # find global cells in argument list,
        # replace them with load variables
        # return a list of load operations
        loadops = []
        for i, arg in enumerate(args):
            if isinstance(arg, Constant) and isinstance(arg.concretetype, mutype.MuGlobalCell):
                ldvar = Variable('ldgcl')
                ldvar.concretetype = arg.concretetype.TO
                loadops.append(self.ll2mu.gen_mu_load(arg, ldvar))
                args[i] = ldvar
        return loadops


# -----------------------------------------------------------------------------
# preparation before mutyper
def graph_closure(g_entry):
    """
    Find closure of graphs from g_entry, including graphs in:
    - direct/indirect calls
    - function references in heap objects

    :param g_entry: the graph in the list that is the entry point
    :return: a set of FunctionGraphs as closure
    """

    graph_closure = set()
    pending_graphs = []
    pending_objects = []
    is_ptr_const = lambda a: isinstance(a, Constant) and isinstance(a.value, lltype._ptr)
    visited_obj = set()

    def _find_funcrefs(obj):
        if isinstance(obj, lltype._ptr):
            refnt = obj._obj
            if isinstance(refnt, lltype._struct):
                refnt = refnt._normalizedcontainer()

            pending_objects.append(refnt)
        else:
            if isinstance(obj, lltype._struct):
                if obj in visited_obj:
                    return
                visited_obj.add(obj)
                fld_dic = lltype.typeOf(obj)._flds
                for fld in fld_dic:
                    _find_funcrefs(obj._getattr(fld))

            elif isinstance(obj, lltype._array):
                if obj in visited_obj:
                    return
                visited_obj.add(obj)
                if isinstance(lltype.typeOf(obj).OF, (lltype.ContainerType, lltype.Ptr)):
                    for i in range(len(obj.items)):
                        itm = obj.getitem(i)
                        _find_funcrefs(itm)

            elif isinstance(obj, lltype._opaque):
                if hasattr(obj, 'container'):
                    _find_funcrefs(obj._normalizedcontainer())

            elif isinstance(obj, llmemory._wref):
                _find_funcrefs(obj._dereference())

            elif isinstance(obj, lltype._func):
                if hasattr(obj, 'graph'):
                    pending_graphs.append(obj.graph)

    def visit(graph):
        if graph in graph_closure:
            return
        graph_closure.add(graph)

        for blk in graph.iterblocks():
            for op in blk.operations:
                if op.opname == 'indirect_call':
                    possible_graphs = op.args[-1].value
                    if possible_graphs:
                        pending_graphs.extend(possible_graphs)

                else:
                    for arg in filter(is_ptr_const, op.args):
                        _find_funcrefs(arg.value)
            for e in blk.exits:
                for arg in filter(is_ptr_const, e.args):
                    _find_funcrefs(arg.value)

        # process all pending objects before moving on to next graph
        while len(pending_objects) > 0:
            obj = pending_objects.pop()
            _find_funcrefs(obj)

    pending_graphs.append(g_entry)
    while len(pending_graphs) > 0:
        graph = pending_graphs.pop()
        visit(graph)

    return graph_closure


def prepare(graphs, entry_graph):
    def _keep_arg(arg, opname=''):
        from rpython.rtyper.lltypesystem.lloperation import LL_OPERATIONS
        _OPS_ALLOW_LLTYPE_ARGS = []
        _OPS_ALLOW_LLTYPE_ARGS += [_op for _op in LL_OPERATIONS if _op.startswith("int_")]
        _OPS_ALLOW_LLTYPE_ARGS += [_op for _op in LL_OPERATIONS if _op.startswith("adr_")]
        _OPS_KEEP_ALL_ARGS = ('setfield', 'setinteriorfield')

        # Returns True if the argument/parameter is to be kept
        if 'malloc' in opname:
            return True
        if 'setfield' in opname:
            return True
        if arg.concretetype != lltype.Void:
            return True
        if isinstance(arg, Constant):
            if isinstance(arg.value, (str, list)):
                return True
            elif isinstance(arg.value, lltype.LowLevelType):
                return opname in _OPS_ALLOW_LLTYPE_ARGS
        if opname in _OPS_KEEP_ALL_ARGS:
            return True
        # log.keep_arg("Throwing argument %(arg)r from operation %(opname)s" % locals())
        return False

    name_dic = {}
    def rename(g):
        """ reassign graph names (shorter names more readable) """
        name = g.name if '.' in g.name else g.name.split('__')[0]
        if name not in name_dic:
            ctr = 0
            name_dic[name] = ([g], ctr)
        else:
            gs, ctr = name_dic[name]
            if g not in gs:
                gs.append(g)
                ctr += 1
                name_dic[name] = (gs, ctr)
        g.name = "%s_%d" % (name, ctr)

    # Task 1: prune and remove inlined graphs
    n0 = len(graphs)
    graphs = graph_closure(entry_graph)
    log.prune("%d -> %d graphs" % (n0, len(graphs)))

    for g in graphs:
        rename(g)

        for blk in list(g.iterblocks()) + [g.returnblock]:  # force include return block, in case always throwing exceptions
            # Task 2: Remove Void args and parameters in inputargs, operations and links
            blk.inputargs = [arg for arg in blk.inputargs if arg.concretetype != lltype.Void]
            for lnk in blk.exits:
                lnk.args = [arg for arg in lnk.args if arg.concretetype != lltype.Void]
            for op in blk.operations:
                op.args = [arg for arg in op.args if _keep_arg(arg, op.opname)]

            # replace constants with dummy variables in inputargs --> they shouldn't appear there
            idx_cnsts = filter(lambda _i: isinstance(blk.inputargs[_i], Constant), range(len(blk.inputargs)))
            if len(idx_cnsts) > 0:
                for i in idx_cnsts:
                    _v = Variable('dummy')
                    _v.concretetype = blk.inputargs[i].concretetype
                    blk.inputargs[i] = _v

    return graphs