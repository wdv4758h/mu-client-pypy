"""
Converts the LLTS types and operations to MuTS.
"""
from rpython.flowspace.model import FunctionGraph, Block, Link, Variable, Constant


class MuTyper:
    def __init__(self):
        pass

    def specialise(self, g):
        for blk in g.iterblocks():
            self.specialise_block(blk)

    def specialise_block(self, blk):
        muops = []
        for arg in blk.inputargs:
            self.proc_var(arg)

    def proc_var(self, var):
        pass
