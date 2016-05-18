"""
Preparations before the MuTyper process
"""
import py
from rpython.mutyper.muts.muentity import MuName
from rpython.rtyper.lltypesystem import lltype
from rpython.flowspace.model import Constant
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

    # A dictionary that maps FunctionGraph -> bool
    ref = {}
    for g in graphs:
        ref[g] = False

    def visit(graph):
        for blk in graph.iterblocks():
            for op in blk.operations:
                if op.opname == 'direct_call':
                    fnc = op.args[0].value._obj
                    try:
                        callee = fnc.graph
                        assert callee in graphs
                        if not ref[callee]:
                            ref[callee] = True
                            visit(callee)
                    except AttributeError:
                        log.error("Error: \"%s\" function does not have a graph" % fnc._name)
                    except AssertionError:
                        log.error("Error: \"%s\" graph not found" % callee._name)
                elif op.opname == 'indirect_call':
                    possible_graphs = op.args[-1].value
                    if possible_graphs:
                        for callee in possible_graphs:
                            try:
                                assert callee in graphs
                                if not ref[callee]:
                                    ref[callee] = True
                                    visit(callee)
                            except AssertionError:
                                log.error("Error: \"%s\" graph not found" % callee._name)

    ref[g_entry] = True
    visit(g_entry)

    return [g for g in graphs if ref[g]]


_OPS_ALLOW_LLTYPE_ARGS = []
_OPS_ALLOW_LLTYPE_ARGS += [op for op in LL_OPERATIONS if op.startswith("int_")]
_OPS_ALLOW_LLTYPE_ARGS += [op for op in LL_OPERATIONS if op.startswith("adr_")]


def prepare(graphs, entry_graph, name_dic={}):
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

        def _keep_arg(arg, opname=''):
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
            log.keep_arg("Throwing argument %(arg)r from operation %(opname)s" % locals())
            return False

        for _, op in g.iterblockops():
            op.args = [arg for arg in op.args if _keep_arg(arg, op.opname)]
            if op.opname == 'cast_pointer':     # fix problem with some cast_pointer ops that don't have CAST_TYPE
                try:
                    assert isinstance(op.args[0], Constant) and isinstance(op.args[0].value, lltype.LowLevelType)
                except AssertionError:
                    op.args.insert(0, Constant(op.result.concretetype, lltype.Void))

        # Remove the Void inputarg in return block and (None) constants in links.
        if g.returnblock.inputargs[0].concretetype == lltype.Void:
            g.returnblock.inputargs = []
            for blk in g.iterblocks():
                for lnk in blk.exits:
                    if lnk.target is g.returnblock:
                        lnk.args = []

        for blk in g.iterblocks():
            # remove the input args that are Void as well.
            blk.inputargs = [arg for arg in blk.inputargs if arg.concretetype != lltype.Void]
    return graphs


def normalise_constant(cnst):
    llv = cnst.value
    llv_norm = _normalise_value(llv)
    if llv_norm is llv:
        return cnst
    Constant.__init__(cnst, llv_norm, lltype.typeOf(llv_norm))


def _normalise_value(llv):
    if not (isinstance(llv, lltype._ptr) and isinstance(llv._obj, lltype._parentable)):
        return llv

    llv = llv._obj._normalizedcontainer()._as_ptr()
    obj = llv._obj
    if isinstance(obj, (lltype._fixedsizearray, lltype._array)):
        n = obj.getlength()
        for i in range(n):
            itm = obj.getitem(i)
            itm_norm = _normalise_value(itm)
            if not (itm_norm is itm):
                obj._TYPE.OF = lltype.typeOf(itm_norm)
                obj.setitem(i, _normalise_value(itm))

    return llv