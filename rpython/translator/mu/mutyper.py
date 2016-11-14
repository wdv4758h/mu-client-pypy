from rpython.flowspace.model import Variable, Constant, c_last_exception
from rpython.rtyper.lltypesystem import lltype, llmemory
from rpython.translator.mu import mutype
from rpython.translator.mu.ll2mu import LL2MuMapper, IgnoredLLOp, IgnoredLLVal
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

        # determine thread local struct type
        tlflds = tlc.annotator.bookkeeper.thread_local_fields
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

        processed = []
        while len(self.graphs) > 0:
            g = self.graphs.pop(0)
            self.specialise_graph(g)
            processed.append(g)

        self.tlc.graphs = self.graphs = processed

    def specialise_graph(self):
        raise NotImplementedError


# -----------------------------------------------------------------------------
# preparation before mutyper
def prune(g_entry):
    """
    Remove all the graphs in the list (after inlining)
    that cannot be reached from the entry point.

    :param g_entry: the graph in the list that is the entry point
    :return: a chopped down list of graphs
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
    graphs = prune(entry_graph)
    log.prune("%d -> %d graphs" % (n0, len(graphs)))

    for g in graphs:
        rename(g)

        for blk in g.iterblocks():
            # Task 2: Remove Void args and parameters in inputargs, operations and links
            blk.inputargs = [arg for arg in blk.inputargs if arg.concretetype != lltype.Void]
            for lnk in blk.exits:
                lnk.args = [arg for arg in lnk.args if arg.concretetype != lltype.Void]
            for op in blk.operations:
                op.args = [arg for arg in op.args if _keep_arg(arg, op.opname)]

                if op.opname == 'cast_pointer':  # explicit CAST_TYPE when it's implicit
                    if not isinstance(op.args[0], Constant) and isinstance(op.args[0].value, lltype.LowLevelType):
                        op.args.insert(0, Constant(op.result.concretetype, lltype.Void))

            # replace constants with dummy variables in inputargs --> they shouldn't appear there
            idx_cnsts = filter(lambda _i: isinstance(blk.inputargs[_i], Constant), range(len(blk.inputargs)))
            if len(idx_cnsts) > 0:
                for i in idx_cnsts:
                    _v = Variable('dummy')
                    _v.concretetype = blk.inputargs[i].concretetype
                    blk.inputargs[i] = _v

    return graphs