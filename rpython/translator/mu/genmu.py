"""
MuIR builder -- builds IR bundle via API calls

This defines an abstract builder that needs to be implemented concretely.
"""
from rpython.mutyper.muts.muentity import MuName
from rpython.tool.ansi_print import AnsiLogger
from rpython.mutyper.muts import mutype, muops
from rpython.mutyper.tools.textgraph import print_graph
from rpython.rlib.rmu import (
    Mu, MuDestKind, MuBinOptr, MuCmpOptr, 
    MuConvOptr, MuMemOrd, MuCallConv, MuCommInst)
from rpython.translator.mu.hail import HAILGenerator
from StringIO import StringIO
import zipfile
import json
from rpython.tool.ansi_mandelbrot import Driver
from mar import mu_meta_set

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
        strio_info = StringIO()
        strio_graphs = StringIO()
        self.codegen(strio_ir, strio_hail, strio_info, strio_graphs)

        self.log.zipbundle("generate zip bundle...")
        zf = zipfile.ZipFile(bdlpath.strpath, mode="w", compression=zip_compression)

        def _writefrom(entry_name, strio):
            s = strio.getvalue()
            strio.close()
            zf.writestr(entry_name, s)

        _writefrom(bdlpath.basename.replace('.mu', '.uir'), strio_ir)
        _writefrom(bdlpath.basename.replace('.mu', '.hail'), strio_hail)
        _writefrom(bdlpath.basename.replace('.mu', '.info'), strio_info)
        _writefrom(bdlpath.basename.replace('.mu', '.txt'), strio_graphs)
        zf.close()
        self.log.zipbundle("done.")

    def codegen(self, fp_ir, fp_hail, fp_info, fp_rpy_graphs=None):
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

        fncs = []
        for extfn in self.db.externfncs:
            fp_ir.write(".const %s <%s> = EXTERN \"%s\"\n" % (extfn.mu_name, extfn._TYPE.mu_name, extfn.c_symname))
            fncs.append((extfn.c_name, str(extfn._TYPE.mu_name), str(extfn.mu_name), extfn.eci.libraries))

        for g in self.graphs:
            fp_ir.write(".funcdef %s VERSION %s <%s> {\n" % (
                g.mu_name, g.mu_version.mu_name, g.mu_type.Sig.mu_name))
            self._genblocks(g, fp_ir)
            fp_ir.write("}\n")

        self.log.codegen("generating HAIL script...")
        # HAIL script
        hailgen = HAILGenerator(self.db.objtracer)
        hailgen.codegen(fp_hail)

        # save the text flow graph
        if fp_rpy_graphs:
            for g in self.graphs:
                print_graph(g, fp_rpy_graphs)

        # some extra information
        info = {
            "libdeps": ":".join(map(lambda lib: lib._name, self.db.dylibs)),
            "entrypoint": str(self.db.prog_entry.mu_name)
        }
        fp_info.write(json.dumps(info))

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
        def get_config_str():
            libconfig = []

            # extraLibs
            extlibs = []
            for lib in db.dylibs:
                extlibs.append(lib._name)
            libconfig.append("extraLibs=" + ":".join(extlibs))

            # dumpBundle
            libconfig.append("dumpBundle=%s" % True)

            return "\n".join(libconfig)

        MuBundleGenerator.__init__(self, db)
        self.gblnode_map = {}
        self.mu = Mu(get_config_str())
        self.ctx = self.mu.new_context()
        self.bdl = None
        self._objhdl_map = {}   # used in heap initialisation; NOTE: referent -> handle (not reference)

    def bundlegen(self, bdlpath):
        self.log.bundlegen("API Bundle generator")

        self.bdl = self.ctx.new_bundle()

        self.gen_types()
        self.gen_consts()
        self.gen_gcells()
        self.gen_graphs()

        wlst = map(lambda nd: self.ctx.get_id(self.bdl, nd),self.gblnode_map.values())
        self.log.bundlegen("load bundle into Mu")
        self.ctx.load_bundle_from_node(self.bdl)

        self.log.bundlegen("start initialise heap objects")
        self.init_heap()

        self.log.bundlegen("start making boot image")
        self.log.bundlegen("%d top level nodes" % len(self.gblnode_map))

        self.mu.make_boot_image(wlst, str(bdlpath))


        mu_meta_set(str(bdlpath),
                    entry_point_name=str(self.db.prog_entry.mu_name),
                    extra_libraries=":".join(map(lambda lib: lib._name, self.db.dylibs)))

    def gen_types(self):
        self.log.gen_types("start generating types.")
        bdl = self.bdl
        ctx = self.ctx
        ref_nodes = []  # 2 pass declaration, need to call set_
        gblndmap = self.gblnode_map
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
        for k, v in gblndmap.items():
            ctx.set_name(bdl, v, str(k.mu_name))

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
                    nd = fn(bdl)
                    ref_nodes.append((t, nd))
                elif isinstance(t, mutype.MuFuncSig):
                    nd = ctx.new_funcsig(bdl, map(_gen_type, t.ARGS), map(_gen_type, t.RTNS))
                else:
                    raise TypeError("Unknown type: %s" % t)
                ctx.set_name(bdl, nd, str(t.mu_name))
                gblndmap[t] = nd
                return nd

        for cls in self.db.gbltypes:
            self.log.gen_types("Generate types under class: %s" % cls)
            for ty in self.db.gbltypes[cls]:
                _gen_type(ty)

        for ref_t, nd in ref_nodes:
            fn = getattr(ctx, "set_type_" + ref_t.__class__.type_constr_name)
            fn(nd, _gen_type(ref_t.Sig if isinstance(ref_t, mutype.MuFuncRef) else ref_t.TO))

    def gen_consts(self):
        self.log.gen_consts("start generating constants")
        self.log.gen_consts("%d constants" % len(self.db.gblcnsts))
        bdl = self.bdl
        ctx = self.ctx
        gblndmap = self.gblnode_map
        for cst in self.db.gblcnsts:
            self.log.gen_consts("generating constant: %s (%s)" % (cst, cst.mu_type))
            assert isinstance(cst.value, (mutype._muprimitive, mutype._munullref))
            if isinstance(cst.mu_type, mutype.MuInt):
                ty = cst.mu_type
                if ty.bits <= 64:
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
                if isinstance(cst.mu_type, mutype.MuUPtr):
                    nd = ctx.new_const_int(bdl, gblndmap[cst.mu_type], 0)
                else:
                    nd = ctx.new_const_null(bdl, gblndmap[cst.mu_type])

            ctx.set_name(bdl, nd, str(cst.mu_name))
            gblndmap[cst] = nd

        for extfn in self.db.externfncs:
            self.log.gen_consts("generating extern function constant: %s" % extfn)
            nd = ctx.new_const_extern(bdl, gblndmap[extfn._TYPE], extfn.c_symname)
            ctx.set_name(bdl, nd, str(extfn.mu_name))
            gblndmap[extfn] = nd

    def gen_graphs(self):
        self.log.gen_graphs("start generating functions")
        bdl = self.bdl
        ctx = self.ctx
        gblndmap = self.gblnode_map

        # declare all functions first
        for g in self.db.graphs:
            nd = ctx.new_func(bdl, gblndmap[g.mu_type.Sig])
            ctx.set_name(bdl, nd, str(g.mu_name))
            gblndmap[g] = nd

        for g in self.db.graphs:
            self.log.gen_graphs("generating function %s" % g)
            fn = ctx.new_func_ver(bdl, gblndmap[g])
            blkmap = {}     # block node map per graph
            # create all block nodes first
            for blk in g.iterblocks():
                bb = ctx.new_bb(fn)
                ctx.set_name(bdl, bb, repr(blk.mu_name))
                blkmap[blk] = bb
                
            for blk in g.iterblocks():
                bb = blkmap[blk]
                varmap = gblndmap.copy()     # local variable nodes map
                for prm in blk.mu_inputargs:
                    nd = ctx.new_nor_param(bb, gblndmap[prm.mu_type])
                    ctx.set_name(bdl, nd, repr(prm.mu_name))
                    varmap[prm] = nd
                if hasattr(blk, 'mu_excparam'):
                    nd = ctx.new_exc_param(bb)
                    ctx.set_name(bdl, nd, repr(blk.mu_excparam.mu_name))
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
                        nd = method(op, bb, varmap, blkmap)

                    if op.result.mu_type is not mutype.void_t:
                        res = ctx.get_inst_res(nd, 0)  # NOTE: things will be difficult when ovf is supported in Mu
                        ctx.set_name(bdl, res, repr(op.result.mu_name))
                        varmap[op.result] = res
                    if op.exc.nor and op.exc.exc:
                        ctx.add_dest(nd, MuDestKind.NORMAL, blkmap[op.exc.nor.blk], map(varmap.get, op.exc.nor.args))
                        ctx.add_dest(nd, MuDestKind.EXCEPT, blkmap[op.exc.exc.blk], map(varmap.get, op.exc.exc.args))

    # NOTE: This should be refactored into a OpGen (visitor?) class
    def _OP_SELECT(self, op, bb, varmap, blkmap):
        return self.ctx.new_select(bb, varmap[op.cond.mu_type], varmap[op.result.mu_type],
                                   varmap[op.cond], varmap[op.ifTrue], varmap[op.ifFalse])

    def _OP_BRANCH(self, op, bb, varmap, blkmap):
        nd = self.ctx.new_branch(bb)
        self.ctx.add_dest(nd, MuDestKind.NORMAL, blkmap[op.dest.blk], map(varmap.get, op.dest.args))
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
        return self.ctx.new_call(bb, varmap[op.callee.mu_type.Sig], varmap[op.callee], map(varmap.get, op.args))

    def _OP_TAILCALL(self, op, bb, varmap, blkmap):
        return self.ctx.new_tailcall(bb, varmap[op.callee.mu_type.Sig], varmap[op.callee], map(varmap.get, op.args))

    def _OP_RET(self, op, bb, varmap, blkmap):
        if op.rv:
            return self.ctx.new_ret(bb, [varmap[op.rv]])
        return self.ctx.new_ret(bb, [])

    def _OP_THROW(self, op, bb, varmap, blkmap):
        return self.ctx.new_throw(bb, varmap[op.excobj])

    def _OP_EXTRACTVALUE(self, op, bb, varmap, blkmap):
        return self.ctx.new_extractvalue(bb, *map(varmap.get, op.opnd.mu_type, op.idx, op.opnd))

    def _OP_INSERTVALUE(self, op, bb, varmap, blkmap):
        return self.ctx.new_insertvalue(bb, *map(varmap.get, op.opnd.mu_type, op.idx, op.opnd, op.val))

    def _OP_EXTRACTELEMENT(self, op, bb, varmap, blkmap):
        return self.ctx.new_extractelement(bb, *map(varmap.get, (op.opnd.mu_type, op.idx.mu_type, op.opnd, op.idx)))

    def _OP_INSERTELEMENT(self, op, bb, varmap, blkmap):
        return self.ctx.new_insertelement(bb, *map(varmap.get, (op.opnd.mu_type, op.idx.mu_type, op.opnd, op.idx, op.val)))

    def _OP_NEW(self, op, bb, varmap, blkmap):
        return self.ctx.new_new(bb, varmap[op.T])

    def _OP_ALLOCA(self, op, bb, varmap, blkmap):
        return self.ctx.new_alloca(bb, varmap[op.T])

    def _OP_NEWHYBRID(self, op, bb, varmap, blkmap):
        return self.ctx.new_newhybrid(bb, varmap[op.T], varmap[op.length.mu_type], varmap[op.length])

    def _OP_ALLOCAHYBRID(self, op, bb, varmap, blkmap):
        return self.ctx.new_allocahybrid(bb, varmap[op.T], varmap[op.length.mu_type], varmap[op.length])

    def _OP_GETIREF(self, op, bb, varmap, blkmap):
        return self.ctx.new_getiref(bb, varmap[op.opnd.mu_type], varmap[op.opnd])

    def _OP_GETFIELDIREF(self, op, bb, varmap, blkmap):
        return self.ctx.new_getfieldiref(bb, isinstance(op.opnd.mu_type, mutype.MuUPtr),
                                         varmap[op.opnd.mu_type.TO], op.idx, varmap[op.opnd])

    def _OP_GETELEMIREF(self, op, bb, varmap, blkmap):
        return self.ctx.new_getelemiref(bb, isinstance(op.opnd.mu_type, mutype.MuUPtr),
                                        *map(varmap.get, (op.opnd.mu_type.TO, op.idx.mu_type, op.opnd, op.idx)))

    def _OP_SHIFTIREF(self, op, bb, varmap, blkmap):
        return self.ctx.new_shiftiref(bb, isinstance(op.opnd.mu_type, mutype.MuUPtr),
                                      *map(varmap.get, (op.opnd.mu_type.TO, op.offset.mu_type, op.opnd, op.offset)))

    def _OP_GETVARPARTIREF(self, op, bb, varmap, blkmap):
        return self.ctx.new_getvarpartiref(bb, isinstance(op.opnd.mu_type, mutype.MuUPtr),
                                           varmap[op.opnd.mu_type.TO], varmap[op.opnd])

    def _OP_LOAD(self, op, bb, varmap, blkmap):
        return self.ctx.new_load(bb, isinstance(op.loc.mu_type, mutype.MuUPtr),
                                 MuMemOrd.NOT_ATOMIC, varmap[op.loc.mu_type.TO], varmap[op.loc])

    def _OP_STORE(self, op, bb, varmap, blkmap):
        return self.ctx.new_store(bb, isinstance(op.loc.mu_type, mutype.MuUPtr),
                                  MuMemOrd.NOT_ATOMIC, varmap[op.loc.mu_type.TO], varmap[op.loc], varmap[op.val])

    def _OP_TRAP(self, op, bb, varmap, blkmap):
        return self.ctx.new_trap(bb, varmap[op.T])

    def _OP_CCALL(self, op, bb, varmap, blkmap):
        return self.ctx.new_ccall(bb, MuCallConv.DEFAULT, varmap[op.callee.mu_type],
                                  varmap[op.callee.mu_type.Sig], varmap[op.callee],
                                  map(varmap.get, op.args))

    def _OP_COMMINST(self, op, bb, varmap, blkmap):
        cls = op.__class__
        if cls is muops.THREAD_EXIT:
            return self.ctx.new_comminst(bb, MuCommInst.UVM_THREAD_EXIT, [], [], [], [])
        elif cls is muops.NATIVE_PIN:
            return self.ctx.new_comminst(bb, MuCommInst.UVM_NATIVE_PIN, [],
                                         [varmap[op.opnd.mu_type]], [], [varmap[op.opnd]])
        elif cls is muops.NATIVE_UNPIN:
            return self.ctx.new_comminst(bb, MuCommInst.UVM_NATIVE_UNPIN, [],
                                         [varmap[op.opnd.mu_type]], [], [varmap[op.opnd]])
        elif cls is muops.NATIVE_EXPOSE:
            return self.ctx.new_comminst(bb, MuCommInst.UVM_NATIVE_EXPOSE, [],
                                         [], [varmap[op.func.mu_type.Sig]],
                                         [varmap[op.func], varmap[op.cookie]])
        elif cls is muops.NATIVE_UNEXPOSE:
            return self.ctx.new_comminst(bb, MuCommInst.UVM_NATIVE_UNEXPOSE, [], [], [], [varmap[op.value]])
        elif cls is muops.GET_THREADLOCAL:
            return self.ctx.new_comminst(bb, MuCommInst.UVM_GET_THREADLOCAL, [], [], [], [])
        elif cls is muops.SET_THREADLOCAL:
            return self.ctx.new_comminst(bb, MuCommInst.UVM_SET_THREADLOCAL, [], [], [], [varmap[op.ref]])
        else:
            raise NotImplementedError("Building method for %s not implemented" % op)

    # NOTE: Heap object initialisation algorithm perhaps should be put into a (visitor?) class
    def gen_gcells(self):
        self.log.gen_gcells("start defining global cells")
        for gcl in self.db.mutyper.ldgcells:
            nd = self.ctx.new_global_cell(self.bdl, self.gblnode_map[gcl._T])
            self.gblnode_map[gcl] = nd
            self.ctx.set_name(self.bdl, nd, str(gcl.mu_name))

    def init_heap(self):
        self._create_heap_objects()

        # store in global cells
        for gcl in self.db.mutyper.ldgcells:
            gcl_id = self.ctx.get_id(self.bdl, self.gblnode_map[gcl])
            hgcl = self.ctx.handle_from_global(gcl_id)
            href = self._objhdl_map[self.db.objtracer.gcells[gcl]]  # object root in gcell -> handle
            self.ctx.store(MuMemOrd.NOT_ATOMIC, hgcl, href)

    def _create_heap_objects(self):
        ctx = self.ctx
        objtracer = self.db.objtracer
        self.log.create_heap_objects("%d objects" % len(objtracer.objs))

        # allocate memory first
        for obj in objtracer.objs:
            type_id = ctx.id_of(str(obj._TYPE.mu_name))
            if isinstance(obj, mutype._muhybrid):
                hlen = ctx.handle_from_uint64(obj.length.val, 64)
                hdl = ctx.new_hybrid(type_id, hlen)
            else:
                hdl = ctx.new_fixed(type_id)

            self._objhdl_map[obj] = hdl # add to handle map

        def _init_obj(obj, hiref=None):
            """
            @param obj: a mutype._muobject
            @return: Mu handle
            """
            print "_init_obj: ", obj
            TYPE = obj._TYPE
            if isinstance(obj, mutype._muprimitive):
                if isinstance(TYPE, mutype.MuInt):
                    if TYPE.bits <= 64:
                        prefix_signed = 's' if obj.val < 0 else 'u'
                        fn = getattr(ctx, "handle_from_%sint%d" % (prefix_signed, TYPE.bits))
                        return fn(obj.val, TYPE.bits)
                    else:
                        val = obj.val
                        words = []
                        while val != 0:
                            words.append(val & 0xFFFFFFFFFFFFFFFF)
                            val >>= 64
                        return ctx.handle_from_uint64s([words], TYPE.bits)
                elif TYPE is mutype.float_t:
                    return ctx.handle_from_float(obj.val)
                elif TYPE is mutype.double_t:
                    return ctx.handle_from_double(obj.val)

            elif isinstance(obj, mutype._munullref):
                const_id = ctx.id_of(str(MuName("%s_%s" % (str(obj), TYPE.mu_name._name))))
                return ctx.handle_from_const(const_id)

            elif isinstance(obj, mutype._mustruct):
                if not hiref:
                    href = self._objhdl_map[obj]
                    hiref = ctx.get_iref(href)
                _init_struct(hiref, obj)

            elif isinstance(obj, mutype._muhybrid):
                if not hiref:
                    href = self._objhdl_map[obj]
                    hiref = ctx.get_iref(href)

                # fixed fields
                for fld_n in obj._TYPE._names[:-1]:
                    fld = getattr(obj, fld_n)
                    fld_iref = ctx.get_field_iref(hiref, obj._TYPE._index_of(fld_n))
                    fld_hdl = _init_obj(fld, fld_iref)
                    if fld_hdl:
                        ctx.store(MuMemOrd.NOT_ATOMIC, fld_iref, fld_hdl)

                # var fields
                arr = getattr(obj, obj._TYPE._varfld)
                if len(arr) > 0:
                    iref_var = ctx.get_var_part_iref(hiref)
                    _init_memarry(iref_var, arr)

            elif isinstance(obj, mutype._muarray):
                href = self._objhdl_map[obj]
                if len(obj) > 0:
                    hiref = ctx.get_iref(href)
                    _init_memarry(hiref, obj)

            elif isinstance(obj, mutype._muref):
                refobj = obj._obj0._top_container() if isinstance(obj._obj0, mutype._mustruct) else obj._obj0
                return self._objhdl_map[refobj]

            elif isinstance(obj, mutype._mufuncref):
                graph = obj.graph
                return ctx.handle_from_func(ctx.id_of(str(graph.mu_name)))

        def _init_memarry(iref_root, arr):
            for i in range(len(arr)):
                elm = arr[i]
                idx_hdl = ctx.handle_from_uint64(i, 64)
                elm_irf = ctx.shift_iref(iref_root, idx_hdl)
                elm_hdl = _init_obj(elm, elm_irf)
                if elm_hdl:
                    ctx.store(MuMemOrd.NOT_ATOMIC, elm_irf, elm_hdl)

        def _init_struct(iref_root, stt):
            # ref = ctx.refcast(ref_root, ctx.id_of(str(stt._TYPE.mu_name)))    # pass in root ref, since substructs should be the first field.
            # iref = ctx.get_iref(ref)
            iref = ctx.refcast(iref_root, ctx.id_of(str(mutype.MuIRef(stt._TYPE).mu_name)))
            for fld_n in stt._TYPE._names:
                fld = getattr(stt, fld_n)
                if isinstance(fld, mutype._mustruct):
                    _init_struct(iref, fld)  # recursively initialise substructs
                else:
                    fld_hdl = _init_obj(fld)
                    fld_iref = ctx.get_field_iref(iref, stt._TYPE._index_of(fld_n))
                    ctx.store(MuMemOrd.NOT_ATOMIC, fld_iref, fld_hdl)


        for obj in objtracer.objs:
            _init_obj(obj)
