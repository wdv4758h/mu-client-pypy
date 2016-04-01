from ..preps import prepare
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
