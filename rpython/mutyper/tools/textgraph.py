""" Text Form Display

"""


def list_entries(lst):
    i = 0
    for e in lst:
        print("%4d %s" % (i, e))
        i += 1


def print_block(b, map_bi):
    print "blk%d" % map_bi[b]
    print "input: [%s]" % (", ".join([str(arg) for arg in b.inputargs]))

    print "operations:"
    for op in b.operations:
        print "%s" % op

    if b.exitswitch:
        print "switch: %s" % b.exitswitch

    print "exits: [%s]" % (", ".join(
        [str(("blk@%d" % map_bi[lnk.target], lnk.args)) for lnk in b.exits]))


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
