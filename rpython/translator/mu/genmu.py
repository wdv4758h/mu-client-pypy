"""
MuIR builder -- builds IR bundle via API calls

This defines an abstract builder that needs to be implemented concretely.
"""
from rpython.tool.ansi_print import AnsiLogger
from rpython.mutyper.muts import mutype, muops
from rpython.mutyper.tools.textgraph import print_graph
from rpython.rlib.rmu import (
    Mu, MuDestKind, MuBinOptr, MuCmpOptr, 
    MuConvOptr, MuCallConv, MuMemOrd, 
    MuCallConv, MuCommInst)
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
        for extfn in self.db.externfncs:
            fp_ir.write(".const %s <%s> = EXTERN \"%s\"\n" % (extfn.mu_name, extfn._TYPE.mu_name, extfn.c_symname))
            fncs.append((extfn.c_name, str(extfn._TYPE.mu_name), str(extfn.mu_name), extfn.eci.libraries))
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
        gblndmap = self.node_map
        gblndmap.update(
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
                return gblndmap[t]
            except KeyError:
                if isinstance(t, mutype.MuStruct):
                    nd = ctx.new_type_struct(bdl, 
                                             map(_gen_type, [t._flds[n] for n in t._names]))
                elif isinstance(t, mutype.MuHybrid):
                    nd = ctx.new_type_hybrid(bdl,
                                             map(_gen_type, [t._flds[n] for n in t._names[:-1]]),
                                             _gen_type(t._flds[t._varfld]))
                elif isinstance(t, mutype.MuArray):
                    nd = ctx.new_type_array(bdl, _gen_type(t.OF), t.length)
                elif isinstance(t, mutype.MuRefType):
                    fn = getattr(ctx, "new_type_" + t.__class__.type_constr_name)
                    nd = fn(ctx, bdl)
                    ref_nodes.append((t, nd))
                elif isinstance(t, mutype.MuFuncSig):
                    nd = ctx.new_funcsig(bdl, map(_gen_type, t.ARGS), map(_gen_type, t.RTNS))
                else:
                    raise TypeError("Unknown type: %s" % t)
                ctx.set_name(bdl, nd, str(t.mu_name))
                gblndmap[t] = nd
                return nd

        for cls in self.db.gbltypes:
            for ty in self.db.gbltypes[cls]:
                _gen_type(ty)

        for ref_t, nd in ref_nodes:
            fn = getattr(ctx, "set_type_" + ref_t.__class__.type_constr_name)
            fn(ctx, nd, _gen_type(ref_t.TO))

    def gen_consts(self):
        bdl = self.bdl
        ctx = self.ctx
        gblndmap = self.node_map
        for cst in self.db.gblcnsts:
            assert isinstance(cst.value, (mutype._muprimitive, mutype._munullref))
            if isinstance(cst.mu_type, mutype.MuInt):
                ty = cst.mu_type
                if ty.bits > 64:
                    nd = ctx.new_const_int(bdl, gblndmap[ty], cst.value.val)

                else:
                    val = cst.value.val
                    words = []
                    while val != 0:
                        words.append(val & 0xFFFFFFFFFFFFFFFF)
                        val >>= 64
                    nd = ctx.new_const_int_ex(bdl, gblndmap[ty], words)
            elif cst.mu_type == mutype.float_t:
                nd = ctx.new_const_float(bdl, gblndmap[cst.mu_type], cst.value.val)
            elif cst.mu_type == mutype.double_t:
                nd = ctx.new_const_double(bdl, gblndmap[cst.mu_type], cst.value.val)
            elif isinstance(cst.value, mutype._munullref):
                nd = ctx.new_const_null(bdl, gblndmap[cst.mu_type])

            ctx.set_name(bdl, nd, str(cst.mu_name))
            gblndmap[cst] = nd

        for extfn in self.db.externfncs:
            nd = ctx.new_const_extern(bdl, gblndmap[extfn._TYPE], extfn.c_symname)
            ctx.set_name(bdl, nd, str(extfn.mu_name))
            gblndmap[extfn] = nd

    def gen_graphs(self):
        bdl = self.bdl
        ctx = self.ctx
        gblndmap = self.node_map
        
        # declare all functions first
        for g in self.db.graphs:
            nd = ctx.new_func(bdl, gblndmap[g.mu_type.Sig])
            ctx.set_name(bdl, nd, str(g.mu_name))
            gblndmap[g] = nd

        for g in self.db.graphs:
            fn = ctx.new_func_ver(bdl, gblndmap[g])
            blkmap = {}     # block node map per graph
            # create all block nodes first
            for blk in g.iterblocks():
                bb = ctx.new_bb(fn)
                ctx.set_name(bdl, bb, str(blk.mu_name))
                blkmap[blk] = bb
                
            for blk in g.iterblocks():
                bb = blkmap[blk]
                varmap = gblndmap.copy()     # local variable nodes map
                for prm in blk.mu_inputargs:
                    nd = ctx.new_nor_param(bb, prm.mu_type)
                    ctx.set_name(bdl, nd, str(prm.mu_name))
                    varmap[prm] = nd
                if hasattr(blk, 'mu_excparam'):
                    nd = ctx.new_exc_param(bb)
                    ctx.set_name(bdl, nd, str(blk.mu_excparam.mu_name))
                    varmap[blk.mu_excparam] = nd
                
                # generate operations
                for op in blk.mu_operations:
                    if op.opname in muops.BINOPS:
                        nd = ctx.new_binop(bb, getattr(MuBinOptr, op.opname), gblndmap[op.op1.mu_type], 
                                           varmap[op.op1], varmap[op.op2])
                    elif op.opname in muops.CMPOPS:
                        nd = ctx.new_cmp(bb, getattr(MuCmpOptr, op.opname), gblndmap[op.op1.mu_type],
                                         varmap[op.op1], varmap[op.op2])
                    elif op.opname in muops.CONVOPS:
                        nd = ctx.new_conv(bb, getattr(MuConvOptr, op.opname), 
                                          gblndmap[op.opnd.mu_type], gblndmap[op.T2], varmap[op.opnd])
                    else:
                        method = getattr(self, '_OP_'+op.opname, None)
                        assert method, "can't find method to build operation " + op.opname
                        nd = method(self, op, bb, varmap, blkmap)

                    res = ctx.get_inst_res(nd, 0)  # NOTE: things will be difficult when ovf is supported in Mu
                    ctx.set_name(bdl, res, str(op.result.mu_name))
                    varmap[op.result] = res

    def _OP_SELECT(self, op, bb, varmap, blkmap):
        return self.ctx.new_select(bb, varmap[op.cond.mu_type], varmap[op.result.mu_type],
                                   varmap[op.cond], varmap[op.ifTrue], varmap[op.ifFalse])
    
    def _OP_BRANCH(self, op, bb, varmap, blkmap):
        nd = self.ctx.new_branch(bb)
        self.ctx.add_dest(nd, MuDestKind.NORMAL, blkmap[op.dst.blk], map(varmap.get, op.dst.args))
        return nd
    
    def _OP_BRANCH2(self, op, bb, varmap, blkmap):
        nd = self.ctx.new_branch2(bb, varmap[op.cond])
        self.ctx.add_dest(nd, MuDestKind.TRUE, blkmap[op.ifTrue.blk], map(varmap.get, op.ifTrue.args))
        self.ctx.add_dest(nd, MuDestKind.FALSE, blkmap[op.ifFalse.blk], map(varmap.get, op.ifFalse.args))
        return nd
    
    def _OP_SWITCH(self, op, bb, varmap, blkmap):
        nd = self.ctx.new_switch(bb, varmap[op.opnd.mu_type], varmap[op.opnd])
        self.ctx.add_dest(nd, MuDestKind.DEFAULT, blkmap[op.default.blk], map(varmap.get, op.default.args))
        for (v, dst) in op.cases:
            self.ctx.add_switch_dest(nd, varmap[v], blkmap[dst.blk], map(varmap.get, dst.args))
        return nd
    
    def _OP_CALL(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_TAILCALL(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_RET(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_THROW(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_EXTRACTVALUE(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_INSERTVALUE(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_EXTRACTELEMENT(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_INSERTELEMENT(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_NEW(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_ALLOCA(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_NEWHYBRID(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_ALLOCAHYBRID(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_GETIREF(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_GETFIELDIREF(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_GETELEMIREF(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_SHIFTIREF(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_GETVARPARTIREF(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_LOAD(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_STORE(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_TRAP(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_CCALL(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_THREAD_EXIT(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_NATIVE_PIN(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_NATIVE_UNPIN(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_NATIVE_EXPOSE(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_NATIVE_UNEXPOSE(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_GET_THREADLOCAL(self, op, bb, varmap, blkmap):
        return self.ctx
    
    def _OP_SET_THREADLOCAL(self, op, bb, varmap, blkmap):
        return self.ctx
        
    
    def gen_gcells(self):
        pass
