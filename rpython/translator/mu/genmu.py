"""
Mu IR text-form generation code
"""
from rpython.flowspace.model import FunctionGraph, Block
from rpython.mutyper.muts.muops import CALL
from rpython.mutyper.muts.mutype import MuFuncRef
from .hail import HAILGenerator


class MuTextIRGenerator:
    BUNDLE_ENTRY_NAME = '_mu_bundle_entry'

    def __init__(self, graphs, mutyper, entry_graph):
        self.graphs = graphs
        self.mutyper = mutyper
        self.prog_entry = entry_graph

        self.bundle_entry = FunctionGraph(MuTextIRGenerator.BUNDLE_ENTRY_NAME, Block(self.prog_entry.startblock.inputargs))
        self.bundle_entry.operations = (CALL(self.prog_entry, *self.bundle_entry.startblock.inputargs),)

    def codegen(self, fp_ir, fp_hail):
        """
        Generate bundle code to a writable file fp.
        """
        for t in self.mutyper.gbltypes:
            if isinstance(t, MuFuncRef):
                fp_ir.write(".funcsig %s = %s\n" % (t.Sig.mu_name, t.Sig.mu_constructor))
                fp_ir.write(".funcdecl %s <%s>\n" % (t.mu_name, t.Sig.mu_name))
            fp_ir.write(".typedef %s = %s\n" % (t.mu_name, t.mu_constructor))

        for c in self.mutyper.gblcnsts:
            fp_ir.write(".const %s = %s\n" % (c.mu_name, c.value))

        hailgen = HAILGenerator()
        for gcell in self.mutyper.ldgcells:
            fp_ir.write(".global %s <%s>\n" % (gcell.mu_name, gcell._T.mu_name))
            hailgen.add_gcell(gcell)
        hailgen.codegen(fp_hail)

        for g in self.graphs:
            fp_ir.write(".funcdef %s VERSION %s <%s> {\n" % (g.mu_name, g.mu_version.mu_name,
                                                             g.mu_type.Sig.mu_name))
            self._genblocks(g, fp_ir)
            fp_ir.write("}\n")

    def _genblocks(self, g, fp):
        idt = 4     # indentation
        for blk in g.iterblocks():
            fp.write('%s%s(%s)%s:\n' % (
                ' ' * idt, blk.mu_name,
                ' '.join(["<%s> %s" % (arg.mu_type.mu_name, arg.mu_name) for arg in blk.inputargs]),
                '[%s]' % blk.mu_excparam if hasattr(blk, 'mu_excparam') else ''
            ))
            for op in blk.operations:
                fp.write("%s%s\n" % (' ' * idt * 2, op))
