"""
Preparations before the MuTyper process
"""
import py
from rpython.mutyper.muts.muentity import MuName
from rpython.rtyper.lltypesystem.lltype import Void, LowLevelType
from rpython.flowspace.model import Constant
from rpython.tool.ansi_print import AnsiLogger

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


def prepare(graphs, entry_graph):
    # Chop graph
    n0 = len(graphs)
    graphs = chop(graphs, entry_graph)
    log.graphchop("%d -> %d graphs" % (n0, len(graphs)))

    name_dic = {}   # {str: ([FunctionGraph], int)}

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

        def _keep_arg(arg):
            # Returns True if the argument/parameter is to be kept
            return arg.concretetype != Void or \
                   (isinstance(arg, Constant) and (isinstance(arg.value, (str, LowLevelType))))
            # (isinstance(arg.value, str) or arg.value is None))

        for _, op in g.iterblockops():
            op.args = [arg for arg in op.args if _keep_arg(arg)]
            if op.opname == 'cast_pointer':     # fix problem with some cast_pointer ops that don't have CAST_TYPE
                try:
                    assert isinstance(op.args[0], Constant) and isinstance(op.args[0].value, LowLevelType)
                except AssertionError:
                    op.args.insert(0, Constant(op.result.concretetype, Void))

        # Remove the Void inputarg in return block and (None) constants in links.
        if g.returnblock.inputargs[0].concretetype == Void:
            g.returnblock.inputargs = []
            for blk in g.iterblocks():
                for lnk in blk.exits:
                    if lnk.target is g.returnblock:
                        lnk.args = []

        for blk in g.iterblocks():
            # remove the input args that are Void as well.
            blk.inputargs = [arg for arg in blk.inputargs if _keep_arg(arg)]
    return graphs
