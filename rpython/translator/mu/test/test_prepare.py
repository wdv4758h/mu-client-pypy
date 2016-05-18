from ..preps import prepare, normalise_constant
from rpython.rlib.objectmodel import specialize
from rpython.rtyper.test.test_llinterp import gengraph
from rpython.mutyper.tools.textgraph import print_graph


def test_graph_rename():
    @specialize.ll()
    def add(a, b):
        return a + b

    def f(s_a, s_b):
        return add(s_a, s_b), add(int(s_a), int(s_b))

    t, _, graph = gengraph(f, [str, str])
    graphs = prepare(t.graphs, graph)
    for g in graphs:
        print_graph(g)

    names = map(lambda g: g.name, graphs)
    assert 'add_0' in names and 'add_1' in names


def test_remove_None_return():
    def f(x):
        print(x + 1)

    t, _, graph = gengraph(f, [int])
    print_graph(graph)
    graphs = prepare(t.graphs, graph)
    assert graph.returnblock.inputargs == []
    assert graph.startblock.exits[0].args == []

    # ----------------------
    def main(argv):
        print argv
        return 0

    t, _, g = gengraph(main, [str])
    graphs = prepare(t.graphs, g)
    op = g.startblock.operations[0]
    g_ll_str = op.args[0].value._obj.graph
    print_graph(g_ll_str)
    assert len(op.args) == 2
    assert len(g_ll_str.startblock.inputargs) == 1


def test_normalise_constant():
    from pyhaskell.interpreter.jscparser import parse_js
    t, _, graph = gengraph(parse_js, [str])

    print_graph(graph)
    cnst = graph.startblock.operations[0].args[0].value._obj.graph.startblock.operations[0].args[0]
    cnst_norm = normalise_constant(cnst)
    assert cnst_norm.concretetype.TO.OF.TO._name != 'object'
    print cnst_norm.value