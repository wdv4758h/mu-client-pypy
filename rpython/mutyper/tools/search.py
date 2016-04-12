"""
Some search functions that might be useful when debugging.
"""
from .textgraph import build_block_index_map


def search_op(graphs, crit_fnc):
    for g in graphs:
        blkidx_map = build_block_index_map(g)
        for b, op in g.iterblockops():
            if crit_fnc(op):
                yield g, blkidx_map[b], op
