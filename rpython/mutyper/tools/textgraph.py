""" Text Form Display

"""

class GraphLister(object):
    def __init__(self, iterable):
        self.lst = list(iterable)

    def grep(self, f):
        if isinstance(f, str):
            return GraphLister([x for x in self.lst if f in str(x)])
        else:
            return GraphLister([x for x in self.lst if f(x)])

    def map_(self, f, *args, **kwargs):
        for e in self.lst:
            f(e, *args, **kwargs)

    def print_graphs(self):
        global print_graph
        self.map_(print_graph)

    def __repr__(self):
        result = []
        for i,e in enumerate(self.lst):
            result.append("%4d %s\n"%(i,str(e)))
        return "".join(result)

class RichTranslation(object):
    def __init__(self, t):
        self.t = t

    def graphs(self, f = None):
        gs = GraphLister(self.t.context.graphs)
        if f != None:
            gs = gs.grep(f)
        return gs

def list_entries(lst):
    i = 0
    for e in lst:
        print("%4d %s" % (i, e))
        i += 1


def print_block(b, map_bi):
    print "blk_%d" % map_bi[b]
    print "input: [%s]" % (", ".join([str(arg) for arg in b.inputargs]))

    print "operations:"
    for op in b.operations:
        print "    %s" % op

    if b.exitswitch:
        print "switch: %s" % b.exitswitch

    print "exits: [%s]" % (", ".join(
        [str(("blk_%d" % map_bi[lnk.target], lnk.args)) for lnk in b.exits]))


def print_graph_with_name(graphs, name):
    for g in graphs:
        if str(g) == name:
            print_graph(g)


def build_block_index_map(g):
    idx = 0
    map_blk_idx = {}

    for b in g.iterblocks():
        map_blk_idx[b] = idx
        idx += 1
    return map_blk_idx


def print_graph(g):
    print '================================================'
    print str(g)

    map_bi = build_block_index_map(g)

    for b in g.iterblocks():
        print '------------------------'
        print_block(b, map_bi)
    print '================================================'
    print
