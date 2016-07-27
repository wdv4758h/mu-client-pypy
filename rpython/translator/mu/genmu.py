"""
MuIR builder -- builds IR bundle via API calls

This defines an abstract builder that needs to be implemented concretely.
"""
from rpython.tool.ansi_print import AnsiLogger
from rpython.mutyper.muts import mutype
from rpython.mutyper.tools.textgraph import print_graph
from rpython.rlib.rmu import Mu
from StringIO import StringIO
import zipfile
import json
from rpython.tool.ansi_mandelbrot import Driver

try:
    import zlib
    zip_compression = zipfile.ZIP_DEFLATED
except ImportError:
    zip_compression = zipfile.ZIP_STORED


__mdb = Driver()

def get_codegen_class():
    from rpython.config.translationoption import get_translation_config
    config = get_translation_config()
    if config.translation.mucodegen == "text":
        return MuTextBundleGenerator
    else:
        return MuAPIBundleGenerator

class MuBundleGenerator:
    def __init__(self, db):
        self.db = db
        self.graphs = db.graphs
        self.log = AnsiLogger(self.__class__.__name__)
        
    def bundlegen(self, bdlpath):
        raise NotImplementedError


class MuTextBundleGenerator(MuBundleGenerator):
    def bundlegen(self, bdlpath):
        strio_ir = StringIO()
        strio_hail = StringIO()
        strio_exfn = StringIO()
        strio_graphs = StringIO()
        self.codegen(strio_ir, strio_hail, strio_exfn, strio_graphs)

        self.log.zipbundle("generate zip bundle...")
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
        self.log.zipbundle("done.")

    def codegen(self, fp_ir, fp_hail, fp_exfn, fp_rpy_graphs=None):
        """
        Generate bundle code to a writable file fp.
        """


        self.log.codegen("generating bundle code...")
        for cls in self.db.gbltypes:
            for t in self.db.gbltypes[cls]:
                fp_ir.write("%s %s = %s\n" % (
                    ".funcsig" if isinstance(t, mutype.MuFuncSig) else ".typedef",
                    t.mu_name, t.mu_constructor))

        for cst in self.db.gblcnsts:
            fp_ir.write(".const %s <%s> = %r\n" % (
                cst.mu_name, cst.mu_type.mu_name, cst.value))

        for gcell in self.db.mutyper.ldgcells:
            fp_ir.write(".global %s <%s>\n" % (gcell.mu_name, gcell._T.mu_name))

        self.db.hailgen.codegen(fp_hail)

        fncs = []
        for gcl in self.db.mutyper.externfncs:
            fp_ir.write(".global %s <%s>\n" % (gcl.mu_name, gcl._T.mu_name))
            fncs.append((gcl.c_name, str(gcl._T.mu_name), str(gcl.mu_name), gcl.c_libs))
        fp_exfn.write(json.dumps(fncs))

        for g in self.graphs:
            fp_ir.write(".funcdef %s VERSION %s <%s> {\n" % (
                g.mu_name, g.mu_version.mu_name, g.mu_type.Sig.mu_name))
            self._genblocks(g, fp_ir)
            fp_ir.write("}\n")

        if fp_rpy_graphs:
            for g in self.graphs:
                print_graph(g, fp_rpy_graphs)

        self.log.codegen("finished.")

    def _genblocks(self, g, fp):
        idt = 4  # indentation
        for blk in g.iterblocks():
            fp.write('%s%s(%s)%s:\n' % (
                ' ' * idt, blk.mu_name,
                ' '.join(["<%s> %s" % (arg.mu_type.mu_name, arg.mu_name)
                          for arg in blk.mu_inputargs]),
                '[%s]' % blk.mu_excparam.mu_name if hasattr(blk, 'mu_excparam') else ''
            ))
            for op in blk.mu_operations:
                fp.write("%s%s\n" % (' ' * idt * 2, op))


# NOTE: when rewriting, use visitor pattern for type generation
class MuAPIBundleGenerator(MuBundleGenerator):
    def __init__(self, db):
        MuBundleGenerator.__init__(self, db)
        self.node_map = {}
        self.mu = Mu()
        self.ctx = self.mu.new_context()
        self.bdl = None

    def bundlegen(self, bdlpath):
        self.log.bundlegen("API Bundle generator")

        self.bdl = self.ctx.new_bundle()

        self.gen_types()
        self.gen_consts()
        self.gen_graphs()
        self.gen_gcells()
        self.mu.make_boot_image([], bdlpath)

    def gen_types(self):
        bdl = self.bdl
        ctx = self.ctx
        ref_nodes = []  # 2 pass declaration, need to call set_
        ndmap = self.node_map
        ndmap.update(
            {
                mutype.int1_t: ctx.new_type_int(bdl, 1),
                mutype.int8_t: ctx.new_type_int(bdl, 8),
                mutype.int16_t: ctx.new_type_int(bdl, 16),
                mutype.int32_t: ctx.new_type_int(bdl, 32),
                mutype.int64_t: ctx.new_type_int(bdl, 64),
                mutype.int128_t: ctx.new_type_int(bdl, 128),
                mutype.float_t: ctx.new_type_float(bdl),
                mutype.double_t: ctx.new_type_double(bdl),
                mutype.void_t: ctx.new_type_void(bdl),
            }
        )

        def _gen_type(t):
            try:
                return ndmap[t]
            except KeyError:
                if isinstance(t, mutype.MuStruct):
                    nd = ctx.new_type_struct(bdl, 
                                             map(_gen_type, [t._flds[n] for n in t._names]))
                    ndmap[t] = nd
                    return nd
                elif isinstance(t, mutype.MuHybrid):
                    nd = ctx.new_type_hybrid(bdl,
                                             map(_gen_type, [t._flds[n] for n in t._names[:-1]]),
                                             _gen_type(t._flds[t._varfld]))
                    ndmap[t] = nd
                    return nd
                elif isinstance(t, mutype.MuArray):
                    nd = ctx.new_type_array(bdl, _gen_type(t.OF), t.length)
                    ndmap[t] = nd
                    return nd
                elif isinstance(t, mutype.MuRefType):
                    fn = getattr(ctx, "new_type_" + t.__class__.type_constr_name)
                    nd = fn(ctx, bdl)
                    ref_nodes.append((t, nd))
                    ndmap[t] = nd
                    return nd
                elif isinstance(t, mutype.MuFuncSig):
                    nd = ctx.new_funcsig(bdl, map(_gen_type, t.ARGS), map(_gen_type, t.RTNS))
                    ndmap[t] = nd
                    return nd
                else:
                    raise TypeError("Unknown type: %s" % t)

        for cls in self.db.gbltypes:
            for ty in self.db.gbltypes[cls]:
                _gen_type(ty)

        for ref_t, nd in ref_nodes:
            fn = getattr(ctx, "set_type_" + ref_t.__class__.type_constr_name)
            fn(ctx, nd, _gen_type(ref_t.TO))

    def gen_consts(self):
        bdl = self.bdl
        ctx = self.ctx
        ndmap = self.node_map
        for cst in self.db.gblcnsts:
            if isinstance(cst.mu_type, mutype.MuInt):
                ty = cst.mu_type
                if ty.bits > 64:
                    ndmap[cst] = ctx.new_const_int(bdl, ndmap[ty], cst.value.val)
                else:
                    val = cst.value.val
                    words = []
                    while val != 0:
                        words.append(val & 0xFFFFFFFFFFFFFFFF)
                        val >>= 64
                    ndmap[cst] = ctx.new_const_int_ex(bdl, ndmap[ty], words)
            elif cst.mu_type == mutype.float_t:
                ndmap[cst] = ctx.new_const_float(bdl, ndmap[cst.mu_type], cst.value.val)
            elif cst.mu_type == mutype.double_t:
                ndmap[cst] = ctx.new_const_double(bdl, ndmap[cst.mu_type], cst.value.val)
            elif isinstance(cst.value, mutype._munullref):
                ndmap[cst] = ctx.new_const_null(bdl, cst.mu_type)
        
    def gen_graphs(self):
        pass

    def gen_gcells(self):
        pass
