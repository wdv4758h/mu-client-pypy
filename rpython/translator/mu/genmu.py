"""
Mu IR text-form generation code
"""
from rpython.flowspace.model import FunctionGraph, Block
from rpython.mutyper.muts.muops import CALL
from rpython.mutyper.muts.mutype import MuFuncRef
from .hail import HAILGenerator
from StringIO import StringIO
import zipfile
import json


try:
    import zlib
    zip_compression = zipfile.ZIP_DEFLATED
except ImportError:
    zip_compression = zipfile.ZIP_STORED


class MuTextIRGenerator:
    BUNDLE_ENTRY_NAME = '_mu_bundle_entry'
    bundle_suffix = '.mu'

    def __init__(self, graphs, mutyper, entry_graph):
        self.graphs = graphs
        self.mutyper = mutyper
        self.prog_entry = entry_graph

        self.bundle_entry = FunctionGraph(MuTextIRGenerator.BUNDLE_ENTRY_NAME, Block(self.prog_entry.startblock.inputargs))
        self.bundle_entry.operations = (CALL(self.prog_entry, *self.bundle_entry.startblock.inputargs),)

    def bundlegen(self, bdlpath):
        strio_ir = StringIO()
        strio_hail = StringIO()
        strio_exfn = StringIO()
        self.codegen(strio_ir, strio_hail, strio_exfn)

        zf = zipfile.ZipFile(bdlpath, mode="w", compression=zip_compression)

        def _writefrom(entry_name, strio):
            s = strio.getvalue()
            strio.close()
            print s
            zf.writestr(entry_name, s)

        _writefrom(bdlpath.replace('.mu', '.ir'), strio_ir)
        _writefrom(bdlpath.replace('.mu', '.hail'), strio_hail)
        _writefrom(bdlpath.replace('.mu', '.exfn'), strio_exfn)

        zf.close()

    def codegen(self, fp_ir, fp_hail, fp_exfn):
        """
        Generate bundle code to a writable file fp.
        """
        for t in self.mutyper.gbltypes:
            if isinstance(t, MuFuncRef):
                fp_ir.write(".funcsig %s = %s\n" % (t.Sig.mu_name, t.Sig.mu_constructor))
            else:
                fp_ir.write(".typedef %s = %s\n" % (t.mu_name, t.mu_constructor))

        for c in self.mutyper.gblcnsts:
            fp_ir.write(".const %s <%s> = %s\n" % (c.mu_name, c.mu_type.mu_name, c.value))

        hailgen = HAILGenerator()
        for gcell in self.mutyper.ldgcells:
            fp_ir.write(".global %s <%s>\n" % (gcell.mu_name, gcell._T.mu_name))
            hailgen.add_gcell(gcell)
        hailgen.codegen(fp_hail)

        fncs = []
        for gcl in self.mutyper.externfncs:
            fp_ir.write(".global %s <%s>\n" % (gcl.mu_name, gcl._T.mu_name))
            fncs.append((gcl.c_name, str(gcl.mu_name), gcl.c_libs))
        fp_exfn.write(json.dumps(fncs))

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
