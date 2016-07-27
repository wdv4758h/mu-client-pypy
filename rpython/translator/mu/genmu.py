"""
MuIR builder -- builds IR bundle via API calls

This defines an abstract builder that needs to be implemented concretely.
"""
from rpython.tool.ansi_print import AnsiLogger
from rpython.mutyper.muts import mutype
from rpython.mutyper.tools.textgraph import print_graph
from StringIO import StringIO
import zipfile
import json
from rpython.tool.ansi_mandelbrot import Driver

log = AnsiLogger("MuTextIRGenerator")

try:
    import zlib
    zip_compression = zipfile.ZIP_DEFLATED
except ImportError:
    zip_compression = zipfile.ZIP_STORED


mdb = Driver()


class MuTextIRBuilder(object):
    def __init__(self, db):
        self.db = db
        self.graphs = db.graphs

    def bundlegen(self, bdlpath):
        strio_ir = StringIO()
        strio_hail = StringIO()
        strio_exfn = StringIO()
        strio_graphs = StringIO()
        self.codegen(strio_ir, strio_hail, strio_exfn, strio_graphs)

        log.zipbundle("generate zip bundle...")
        zf = zipfile.ZipFile(bdlpath.strpath, mode="w", compression=zip_compression)

        def _writefrom(entry_name, strio):
            s = strio.getvalue()
            strio.close()
            zf.writestr(entry_name, s)

        _writefrom(bdlpath.basename.replace('.mu', '.uir'), strio_ir)
        _writefrom(bdlpath.basename.replace('.mu', '.hail'), strio_hail)
        _writefrom(bdlpath.basename.replace('.mu', '.exfn'), strio_exfn)
        _writefrom(bdlpath.basename.replace('.mu', '.txt'), strio_graphs)
        zf.close()
        log.zipbundle("done.")

    def codegen(self, fp_ir, fp_hail, fp_exfn, fp_rpy_graphs=None):
        """
        Generate bundle code to a writable file fp.
        """


        log.codegen("generating bundle code...")
        for cls in self.db.gbltypes:
            for t in self.db.gbltypes[cls]:
                fp_ir.write("%s %s = %s\n" % (".funcsig" if isinstance(t, mutype.MuFuncSig) else ".typedef",
                                              t.mu_name, t.mu_constructor))

        for cst in self.db.gblcnsts:
            fp_ir.write(".const %s <%s> = %r\n" % (cst.mu_name, cst.mu_type.mu_name, cst.value))

        for gcell in self.db.mutyper.ldgcells:
            fp_ir.write(".global %s <%s>\n" % (gcell.mu_name, gcell._T.mu_name))

        self.db.hailgen.codegen(fp_hail)

        fncs = []
        for extfn in self.db.externfncs:
            fp_ir.write(".const %s <%s> = EXTERN \"%s\"\n" % (extfn.mu_name, extfn._TYPE.mu_name, extfn.c_name))
            fncs.append((extfn.c_name, str(extfn._TYPE.mu_name), str(extfn.mu_name), extfn.eci.libraries))
        fp_exfn.write(json.dumps(fncs))

        for g in self.graphs:
            fp_ir.write(".funcdef %s VERSION %s <%s> {\n" % (g.mu_name, g.mu_version.mu_name,
                                                             g.mu_type.Sig.mu_name))
            self._genblocks(g, fp_ir)
            fp_ir.write("}\n")

        if fp_rpy_graphs:
            for g in self.graphs:
                print_graph(g, fp_rpy_graphs)

        log.codegen("finished.")

    def _genblocks(self, g, fp):
        idt = 4  # indentation
        for blk in g.iterblocks():
            fp.write('%s%s(%s)%s:\n' % (
                ' ' * idt, blk.mu_name,
                ' '.join(["<%s> %s" % (arg.mu_type.mu_name, arg.mu_name) for arg in blk.mu_inputargs]),
                '[%s]' % blk.mu_excparam.mu_name if hasattr(blk, 'mu_excparam') else ''
            ))
            for op in blk.mu_operations:
                fp.write("%s%s\n" % (' ' * idt * 2, op))
