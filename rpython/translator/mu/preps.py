"""
Preparations before the MuTyper process
"""
from rpython.rtyper.lltypesystem import lltype
from rpython.flowspace.model import Constant, Variable
from rpython.tool.ansi_print import AnsiLogger
from rpython.rtyper.lltypesystem.lloperation import LL_OPERATIONS

log = AnsiLogger("preps")


def chop(graphs, g_entry):
    """
    Remove all the graphs in the list (after inlining)
    that cannot be reached from the entry point.

    :param graphs: A list of rpython.flowspace.model.FunctionGraph (after backendopt.inline)
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


_OPS_ALLOW_LLTYPE_ARGS = []
_OPS_ALLOW_LLTYPE_ARGS += [_op for _op in LL_OPERATIONS if _op.startswith("int_")]
_OPS_ALLOW_LLTYPE_ARGS += [_op for _op in LL_OPERATIONS if _op.startswith("adr_")]


def _keep_arg(arg, opname=''):
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


def prepare(graphs, entry_graph, name_dic={}):
    _cnsts = {}
    def _replace_consts_in_list(lst):
        # Make all constants that have the same hash the same object
        for _i in filter(lambda idx: isinstance(lst[idx], Constant), range(len(lst))):
            c = lst[_i]
            if c not in _cnsts:
                _cnsts[c] = c
            else:
                assert c == _cnsts[c]
                lst[_i] = _cnsts[c]

    # Chop graph
    n0 = len(graphs)
    graphs = chop(graphs, entry_graph)
    log.graphchop("%d -> %d graphs" % (n0, len(graphs)))

    for g in graphs:
        # Assign names
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

        for blk in g.iterblocks():
            # remove the input args that are Void as well.
            blk.mu_inputargs = [arg for arg in blk.inputargs if arg.concretetype != lltype.Void]
            # replace constants with dummy variables --> they shouldn't appear there
            idx_cnsts = filter(lambda _i: isinstance(blk.mu_inputargs[_i], Constant), range(len(blk.mu_inputargs)))
            if len(idx_cnsts) > 0:
                for i in idx_cnsts:
                    _v = Variable('dummy')
                    _v.concretetype = blk.mu_inputargs[i].concretetype
                    blk.mu_inputargs[i] = _v

            for op in blk.operations:
                op.args = [arg for arg in op.args if _keep_arg(arg, op.opname)]
                if op.opname == 'cast_pointer':  # fix problem with some cast_pointer ops that don't have CAST_TYPE
                    try:
                        assert isinstance(op.args[0], Constant) and isinstance(op.args[0].value,
                                                                               lltype.LowLevelType)
                    except AssertionError:
                        op.args.insert(0, Constant(op.result.concretetype, lltype.Void))

                _replace_consts_in_list(op.args)

            # set the mu_arg attribute for every links
            for lnk in blk.exits:
                lnk.mu_args = [arg for arg in lnk.args if arg.concretetype != lltype.Void]
                _replace_consts_in_list(lnk.mu_args)

        if not hasattr(g.returnblock, 'mu_inputargs'):
            g.returnblock.mu_inputargs = [arg for arg in g.returnblock.inputargs if arg.concretetype != lltype.Void]

    return graphs
