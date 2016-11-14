from rpython.translator.mu.mutyper import *
from rpython.translator.interactive import Translation

def graph_of(f, t):
    return t.context.annotator.bookkeeper.getdesc(f).getuniquegraph()

def test_prune():
    def g(x):
        return x * (x + 1)
    def f(x):
        return 3 * g(x) + 8

    t = Translation(f, [int])
    t.rtype()
    graphs = t.context.graphs
    graph_f = graph_of(f, t)

    assert len(prune(graphs, graph_f)) == 2     # pruned out ll_runtime_type_info, ll_issubclass, ll_type
    t.backendopt()  # this should inline g
    assert len(prune(graphs, graph_f)) == 1     # pruned g


def test_prune_preserve_func_references():
    def add1(x): return x + 1
    def add2(x): return x + 2
    def add3(x): return x + 3
    fncs = {
        '1': add1,
        '2': add2,
        '3': add3
    }

    def f(x, k):
        g = fncs[str(k)]
        return g(x)

    t = Translation(f, [int, int])
    t.rtype()
    graphs = t.context.graphs
    graph_f = graph_of(f, t)
    graph_add1 = graph_of(add1, t)
    graph_add2 = graph_of(add2, t)
    graph_add3 = graph_of(add3, t)

    assert len(prune(graphs, graph_f)) < len(graphs)
    assert graph_add1 in graphs
    assert graph_add2 in graphs
    assert graph_add3 in graphs
