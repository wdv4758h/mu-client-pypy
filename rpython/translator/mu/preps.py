"""
Preparations before the MuTyper process
"""
import py
from rpython.tool.ansi_print import ansi_log
from rpython.translator.mu.mutyper.muts.name import Name

log = py.log.Producer("preps")
py.log.setconsumer("preps", ansi_log)


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
                    for callee in op.args[-1]:
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

    # Assign names
    for g in graphs:
        # Generate name
        name = g.name if '.' in g.name else g.name.split('__')[0]
        line_no = g.startline
        g.muname = Name("%s_%s" % (line_no, name))

        # TODO: g.musig = MuFuncSig(...)

        for idx, blk in enumerate(list(g.iterblocks())):
            blk.muname = Name("blk%d" % idx, g)
            for var in blk.getvariables():
                var.muname = Name(var.name, blk)
            for cst in blk.getconstants():
                cst.muname = Name("cst", blk)

    return graphs
