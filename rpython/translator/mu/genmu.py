"""
MuIR builder -- builds IR bundle via API calls

This defines an abstract builder that needs to be implemented concretely.
"""
from rpython.mutyper.muts.muentity import MuName
from rpython.tool.ansi_print import AnsiLogger
from rpython.mutyper.muts import mutype, muops
from rpython.mutyper.tools.textgraph import print_graph
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
    cls_map = {
        "text": MuTextBundleGenerator,
        "api": MuAPIBundleGenerator,
        "c": MuCSourceBundleGenerator,
    }
    return cls_map[config.translation.mucodegen]

def get_rmu():
    from rpython.config.translationoption import get_translation_config
    config = get_translation_config()
    if config.translation.muimpl == 'ref':
        from rpython.rlib import rmu, rmu_genc
    else:
        from rpython.rlib import rmu_fast as rmu
        from rpython.rlib import rmu_genc_fast as rmu_genc
    return rmu, rmu_genc

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

        _writefrom(bdlpath.basename.replace(bdlpath.ext, '.uir'), strio_ir)
        _writefrom(bdlpath.basename.replace(bdlpath.ext, '.hail'), strio_hail)
        _writefrom(bdlpath.basename.replace(bdlpath.ext, '.info'), strio_info)
        _writefrom(bdlpath.basename.replace(bdlpath.ext, '.txt'), strio_graphs)
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
            "entrypoint": str(self.db.prog_entry.mu_name),
            "argv_t": str(self.db.prog_entry.startblock.mu_inputargs[1].mu_type.mu_name)
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
    _genc = False
    _newline = '\n'
    def __init__(self, db):
        MuBundleGenerator.__init__(self, db)
        self.idmap = {}
        if self.__class__._genc:
            _, self._rmu = get_rmu()
        else:
            self._rmu, _ = get_rmu()
        try:
            self.mu = self._rmu.MuVM(self.get_config_str(db))
        except TypeError:   # no argument needed -> rmu_fast
            self.mu = self._rmu.MuVM()
        self.ctx = self.mu.new_context()
        self.bdr = None
        self._objhdl_map = {}   # used in heap initialisation; NOTE: referent -> handle (not reference)

    def get_config_str(self, db):
        libconfig = []

        # extraLibs
        extlibs = []
        for lib in db.dylibs:
            extlibs.append(lib._name)
        libconfig.append("extraLibs=" + ":".join(extlibs))

        # dumpBundle
        libconfig.append("dumpBundle=%s" % False)

        # silent
        libconfig.append("vmLog=ERROR")
        return self.__class__._newline.join(libconfig)

    def bundlegen(self, bdlpath):
        self.log.bundlegen("API Bundle generator")

        self.bdr = self.ctx.new_ir_builder()

        self.gen_types()
        self.gen_consts()
        self.gen_gcells()
        self.gen_graphs()

        self.log.bundlegen("load bundle into Mu")
        self.bdr.load()

        self.log.bundlegen("start initialise heap objects")
        self.init_heap()

        self.log.bundlegen("start making boot image")
        self.log.bundlegen("%d top level nodes" % len(self.idmap))

        from rpython.config.translationoption import get_translation_config
        config = get_translation_config()
        if config.translation.mutestjit:
            from rpython.translator.platform import platform
            libpath = bdlpath.dirpath().join(bdlpath.basename.replace(bdlpath.ext, '.' + platform.so_ext))
            self.mu.compile_to_sharedlib(libpath)
        else:
            hmain = self.ctx.handle_from_func(self.idmap[self.db.prog_entry])
            self.ctx.make_boot_image(self.idmap.values(), hmain,
                                     self._rmu.null(self._rmu.MuStackRefValue), self._rmu.null(self._rmu.MuRefValue),
                                     [], [], [], [], str(bdlpath))

        if hasattr(self.mu, 'close'):
            self.mu.close()

        self.extras(bdlpath)

    def extras(self, bdlpath):
        mu_meta_set(str(bdlpath),
                    extra_libraries=":".join(map(lambda lib: lib._name, self.db.dylibs)))

    def gen_types(self):
        self.log.gen_types("start generating types.")
        bdr = self.bdr
        ref_nodes = []  # 2 pass declaration, need to call set_
        idmap = self.idmap

        # primitive types
        prelude = (
            ".typedef {int1_t.mu_name} = int<1>%(newline)s"
            ".typedef {int8_t.mu_name} = int<8>%(newline)s"
            ".typedef {int16_t.mu_name} = int<16>%(newline)s"
            ".typedef {int32_t.mu_name} = int<32>%(newline)s"
            ".typedef {int64_t.mu_name} = int<64>%(newline)s"
            ".typedef {int128_t.mu_name} = int<128>%(newline)s"
            ".typedef {float_t.mu_name} = float%(newline)s"
            ".typedef {double_t.mu_name} = double%(newline)s"
            ".typedef {void_t.mu_name} = void%(newline)s"
        ).format(**mutype.__dict__) % {'newline': self.__class__._newline}

        self.ctx.load_bundle(prelude)
        for t in (
                mutype.int1_t,
                mutype.int8_t,
                mutype.int16_t,
                mutype.int32_t,
                mutype.int64_t,
                mutype.int128_t,
                mutype.float_t,
                mutype.double_t,
                mutype.void_t):
            idmap[t] = self.ctx.id_of(str(t.mu_name))

        def _gen_type(t):
            try:
                return idmap[t]
            except KeyError:
                _id = bdr.gen_sym(str(t.mu_name))
                if isinstance(t, mutype.MuStruct):
                    bdr.new_type_struct(_id, map(_gen_type, [t._flds[n] for n in t._names]))
                elif isinstance(t, mutype.MuHybrid):
                    bdr.new_type_hybrid(_id, map(_gen_type, [t._flds[n] for n in t._names[:-1]]),
                                        _gen_type(t._flds[t._varfld]))
                elif isinstance(t, mutype.MuArray):
                    bdr.new_type_array(_id, _gen_type(t.OF), t.length)
                elif isinstance(t, mutype.MuRefType):
                    ref_nodes.append((t, _id))
                elif isinstance(t, mutype.MuFuncSig):
                    bdr.new_funcsig(_id, map(_gen_type, t.ARGS), map(_gen_type, t.RTNS))
                else:
                    raise TypeError("Unknown type: %s" % t)
                idmap[t] = _id
                return _id

        for cls in self.db.gbltypes:
            self.log.gen_types("Generate types under class: %s" % cls)
            for ty in self.db.gbltypes[cls]:
                _gen_type(ty)

        for ref_t, _id in ref_nodes:
            fn = getattr(bdr, "new_type_" + ref_t.__class__.type_constr_name)
            fn(_id, _gen_type(ref_t.Sig if isinstance(ref_t, mutype.MuFuncRef) else ref_t.TO))

    def gen_consts(self):
        self.log.gen_consts("start generating constants")
        self.log.gen_consts("%d constants" % len(self.db.gblcnsts))
        bdr = self.bdr
        idmap = self.idmap
        for cst in self.db.gblcnsts:
            self.log.gen_consts("generating constant: %s (%s)" % (cst, cst.mu_type))
            assert isinstance(cst.value, (mutype._muprimitive, mutype._munullref))
            _id = bdr.gen_sym(str(cst.mu_name))

            if isinstance(cst.mu_type, mutype.MuInt):
                ty = cst.mu_type
                if ty.bits <= 64:
                    bdr.new_const_int(_id, idmap[ty], cst.value.val)
                else:
                    val = cst.value.val
                    words = []
                    while val != 0:
                        words.append(val & 0xFFFFFFFFFFFFFFFF)
                        val >>= 64
                    bdr.new_const_int_ex(_id, idmap[ty], words)
            elif cst.mu_type == mutype.float_t:
                bdr.new_const_float(_id, idmap[cst.mu_type], cst.value.val)
            elif cst.mu_type == mutype.double_t:
                bdr.new_const_double(_id, idmap[cst.mu_type], cst.value.val)
            elif isinstance(cst.value, mutype._munullref):
                if isinstance(cst.mu_type, mutype.MuUPtr):
                    bdr.new_const_int(_id, idmap[cst.mu_type], 0)
                else:
                    bdr.new_const_null(_id, idmap[cst.mu_type])

            idmap[cst] = _id

        for extfn in self.db.externfncs:
            self.log.gen_consts("generating extern function constant: %s" % extfn)
            _id = bdr.gen_sym(str(extfn.mu_name))
            bdr.new_const_extern(_id, idmap[extfn._TYPE], extfn.c_symname)
            idmap[extfn] = _id

    def gen_graph(self, g):
        bdr = self.bdr
        idmap = self.idmap

        self.log.gen_graphs("generating function %s" % g)
        fn = bdr.gen_sym(str(g.mu_name) + '_v1')

        blkmap = {}  # block node map per graph
        # create all block nodes first
        blks = []
        for blk in g.iterblocks():
            bb = bdr.gen_sym(repr(blk.mu_name))
            blkmap[blk] = bb
            blks.append(bb)
        bdr.new_func_ver(fn, idmap[g], blks)

        for blk in g.iterblocks():
            self.gen_block(blk, blkmap)

    def gen_block(self, blk, blkmap):
        idmap = self.idmap
        bdr = self.bdr

        bb = blkmap[blk]
        varmap = idmap.copy()  # local variable nodes map

        nor_prms = []
        nor_prm_ts = []
        for prm in blk.mu_inputargs:
            _id = bdr.gen_sym(repr(prm.mu_name))
            nor_prms.append(_id)
            nor_prm_ts.append(idmap[prm.mu_type])
            varmap[prm] = _id
        if hasattr(blk, 'mu_excparam'):
            exc_prm_id = bdr.gen_sym(repr(blk.mu_excparam.mu_name))
            varmap[blk.mu_excparam] = exc_prm_id
        else:
            exc_prm_id = self._rmu.MU_NO_ID

        # generate operations
        op_ids = []
        for op in blk.mu_operations:
            _id = bdr.gen_sym()
            op_ids.append(_id)

            res = bdr.gen_sym(repr(op.result.mu_name)) if not op.result.mu_type is mutype.void_t else self._rmu.MU_NO_ID
            varmap[op.result] = res

            if op.exc.nor and op.exc.exc:
                _nor = bdr.gen_sym()
                _exc = bdr.gen_sym()
                exc = bdr.gen_sym()
                bdr.new_dest_clause(_nor, blkmap[op.exc.nor.blk], map(varmap.get, op.exc.nor.args))
                bdr.new_dest_clause(_exc, blkmap[op.exc.exc.blk], map(varmap.get, op.exc.exc.args))
                bdr.new_exc_clause(exc, _nor, _exc)
            else:
                exc = self._rmu.MU_NO_ID

            if op.opname in muops.BINOPS:
                bdr.new_binop(_id, res, getattr(self._rmu.MuBinOptr, op.opname), idmap[op.op1.mu_type],
                                varmap[op.op1], varmap[op.op2], exc)
            elif op.opname in muops.CMPOPS:
                bdr.new_cmp(_id, res, getattr(self._rmu.MuCmpOptr, op.opname), idmap[op.op1.mu_type],
                            varmap[op.op1], varmap[op.op2])
            elif op.opname in muops.CONVOPS:
                bdr.new_conv(_id, res, getattr(self._rmu.MuConvOptr, op.opname),
                                idmap[op.opnd.mu_type], idmap[op.T2], varmap[op.opnd])
            else:
                method = getattr(self, '_OP_' + op.opname, None)
                assert method, "can't find method to build operation " + op.opname
                method(_id, op, varmap, blkmap=blkmap, exc=exc)

        bdr.new_bb(bb, nor_prms, nor_prm_ts, exc_prm_id, op_ids)

    def gen_graphs(self):
        self.log.gen_graphs("start generating functions")
        bdr = self.bdr
        idmap = self.idmap

        # declare all functions first
        for g in self.db.graphs:
            _id = bdr.gen_sym(str(g.mu_name))
            bdr.new_func(_id, idmap[g.mu_type.Sig])
            idmap[g] = _id

        for g in self.db.graphs:
            self.gen_graph(g)

    # NOTE: This should be refactored into a OpGen (visitor?) class
    def _OP_SELECT(self, op_id, op, varmap, **kwargs):
        self.bdr.new_select(op_id, varmap[op.result], varmap[op.cond.mu_type], varmap[op.result.mu_type],
                            varmap[op.cond], varmap[op.ifTrue], varmap[op.ifFalse])

    def _OP_BRANCH(self, op_id, op, varmap, **kwargs):
        blkmap = kwargs['blkmap']
        dest = self.bdr.gen_sym()
        self.bdr.new_dest_clause(dest, blkmap[op.dest.blk], map(varmap.get, op.dest.args))
        self.bdr.new_branch(op_id, dest)

    def _OP_BRANCH2(self, op_id, op, varmap, **kwargs):
        blkmap = kwargs['blkmap']
        dst_t = self.bdr.gen_sym()
        dst_f = self.bdr.gen_sym()
        self.bdr.new_dest_clause(dst_t, blkmap[op.ifTrue.blk], map(varmap.get, op.ifTrue.args))
        self.bdr.new_dest_clause(dst_f, blkmap[op.ifFalse.blk], map(varmap.get, op.ifFalse.args))
        self.bdr.new_branch2(op_id, varmap[op.cond], dst_t, dst_f)

    def _OP_SWITCH(self, op_id, op, varmap, **kwargs):
        blkmap = kwargs['blkmap']
        dst_defl = self.bdr.gen_sym()
        self.bdr.new_dest_clause(dst_defl, blkmap[op.default.blk], map(varmap.get, op.default.args))
        consts = []
        dsts = []
        for (v, dst) in op.cases:
            _dst = self.bdr.gen_sym()
            self.bdr.new_dest_clause(_dst, blkmap[dst.blk], map(varmap.get, dst.args))
            consts.append(varmap[v])
            dsts.append(_dst)

        self.bdr.new_switch(op_id, varmap[op.opnd.mu_type], varmap[op.opnd], dst_defl, consts, dsts)

    def _OP_CALL(self, op_id, op, varmap, **kwargs):
        res = varmap[op.result]
        self.bdr.new_call(op_id, [res] if not res is self._rmu.MU_NO_ID else [], varmap[op.callee.mu_type.Sig],
                          varmap[op.callee], map(varmap.get, op.args), exc_clause=kwargs['exc'])

    def _OP_TAILCALL(self, op_id, op, varmap, **kwargs):
        self.bdr.new_tailcall(op_id, varmap[op.callee.mu_type.Sig], varmap[op.callee], map(varmap.get, op.args))

    def _OP_RET(self, op_id, op, varmap, **kwargs):
        if op.rv:
            self.bdr.new_ret(op_id, [varmap[op.rv]])
        else:
            self.bdr.new_ret(op_id, [])

    def _OP_THROW(self, op_id, op, varmap, **kwargs):
        self.bdr.new_throw(op_id, varmap[op.excobj])

    def _OP_EXTRACTVALUE(self, op_id, op, varmap, **kwargs):
        self.bdr.new_extractvalue(op_id, varmap[op.result], *map(varmap.get, op.opnd.mu_type, op.idx, op.opnd))

    def _OP_INSERTVALUE(self, op_id, op, varmap, **kwargs):
        self.bdr.new_insertvalue(op_id, varmap[op.result], *map(varmap.get, op.opnd.mu_type, op.idx, op.opnd, op.val))

    def _OP_EXTRACTELEMENT(self, op_id, op, varmap, **kwargs):
        self.bdr.new_extractelement(op_id, varmap[op.result], *map(varmap.get, (op.opnd.mu_type, op.idx.mu_type, op.opnd, op.idx)))

    def _OP_INSERTELEMENT(self, op_id, op, varmap, **kwargs):
        self.bdr.new_insertelement(op_id, varmap[op.result], *map(varmap.get, (op.opnd.mu_type, op.idx.mu_type, op.opnd, op.idx, op.val)))

    def _OP_NEW(self, op_id, op, varmap, **kwargs):
        self.bdr.new_new(op_id, varmap[op.result], varmap[op.T])

    def _OP_ALLOCA(self, op_id, op, varmap, **kwargs):
        self.bdr.new_alloca(op_id, varmap[op.result], varmap[op.T])

    def _OP_NEWHYBRID(self, op_id, op, varmap, **kwargs):
        self.bdr.new_newhybrid(op_id, varmap[op.result], varmap[op.T], varmap[op.length.mu_type], varmap[op.length])

    def _OP_ALLOCAHYBRID(self, op_id, op, varmap, **kwargs):
        self.bdr.new_allocahybrid(op_id, varmap[op.result], varmap[op.T], varmap[op.length.mu_type], varmap[op.length])

    def _OP_GETIREF(self, op_id, op, varmap, **kwargs):
        self.bdr.new_getiref(op_id, varmap[op.result], varmap[op.opnd.mu_type], varmap[op.opnd])

    def _OP_GETFIELDIREF(self, op_id, op, varmap, **kwargs):
        self.bdr.new_getfieldiref(op_id, varmap[op.result], isinstance(op.opnd.mu_type, mutype.MuUPtr),
                                  varmap[op.opnd.mu_type.TO], op.idx, varmap[op.opnd])

    def _OP_GETELEMIREF(self, op_id, op, varmap, **kwargs):
        self.bdr.new_getelemiref(op_id, varmap[op.result], isinstance(op.opnd.mu_type, mutype.MuUPtr),
                                 *map(varmap.get, (op.opnd.mu_type.TO, op.idx.mu_type, op.opnd, op.idx)))

    def _OP_SHIFTIREF(self, op_id, op, varmap, **kwargs):
        self.bdr.new_shiftiref(op_id, varmap[op.result], isinstance(op.opnd.mu_type, mutype.MuUPtr),
                               *map(varmap.get, (op.opnd.mu_type.TO, op.offset.mu_type, op.opnd, op.offset)))

    def _OP_GETVARPARTIREF(self, op_id, op, varmap, **kwargs):
        self.bdr.new_getvarpartiref(op_id, varmap[op.result], isinstance(op.opnd.mu_type, mutype.MuUPtr),
                                    varmap[op.opnd.mu_type.TO], varmap[op.opnd])

    def _OP_LOAD(self, op_id, op, varmap, **kwargs):
        self.bdr.new_load(op_id, varmap[op.result], isinstance(op.loc.mu_type, mutype.MuUPtr),
                          self._rmu.MuMemOrd.NOT_ATOMIC, varmap[op.loc.mu_type.TO], varmap[op.loc])

    def _OP_STORE(self, op_id, op, varmap, **kwargs):
        self.bdr.new_store(op_id, isinstance(op.loc.mu_type, mutype.MuUPtr),
                           self._rmu.MuMemOrd.NOT_ATOMIC, varmap[op.loc.mu_type.TO], varmap[op.loc], varmap[op.val])

    def _OP_TRAP(self, op_id, op, varmap, **kwargs):
        # self.bdr.new_trap(op_id, varmap[op.T])
        raise NotImplementedError

    def _OP_CCALL(self, op_id, op, varmap, **kwargs):
        res = varmap[op.result]
        self.bdr.new_ccall(op_id, [res] if not res is self._rmu.MU_NO_ID else [], self._rmu.MuCallConv.DEFAULT, varmap[op.callee.mu_type],
                           varmap[op.callee.mu_type.Sig], varmap[op.callee], map(varmap.get, op.args))

    def _OP_COMMINST(self, op_id, op, varmap, **kwargs):
        cls = op.__class__
        if cls is muops.THREAD_EXIT:
            self.bdr.new_comminst(op_id, [], self._rmu.MuCommInst.THREAD_EXIT, [], [], [], [])
        elif cls is muops.NATIVE_PIN:
            self.bdr.new_comminst(op_id, [varmap[op.result]], self._rmu.MuCommInst.NATIVE_PIN, [],
                                         [varmap[op.opnd.mu_type]], [], [varmap[op.opnd]])
        elif cls is muops.NATIVE_UNPIN:
            self.bdr.new_comminst(op_id, [], self._rmu.MuCommInst.NATIVE_UNPIN, [],
                                         [varmap[op.opnd.mu_type]], [], [varmap[op.opnd]])
        # elif cls is muops.NATIVE_EXPOSE:
        #     self.bdr.new_comminst(op_id, [], MuCommInst.NATIVE_EXPOSE, [],
        #                                  [], [varmap[op.func.mu_type.Sig]],
        #                                  [varmap[op.func], varmap[op.cookie]])
        # elif cls is muops.NATIVE_UNEXPOSE:
        #     self.bdr.new_comminst(op_id, [], MuCommInst.NATIVE_UNEXPOSE, [], [], [], [varmap[op.value]])
        elif cls is muops.GET_THREADLOCAL:
            self.bdr.new_comminst(op_id, [varmap[op.result]], self._rmu.MuCommInst.GET_THREADLOCAL, [], [], [], [])
        elif cls is muops.SET_THREADLOCAL:
            self.bdr.new_comminst(op_id, [], self._rmu.MuCommInst.SET_THREADLOCAL, [], [], [], [varmap[op.ref]])
        else:
            raise NotImplementedError("Building method for %s not implemented" % op)

    # NOTE: Heap object initialisation algorithm perhaps should be put into a (visitor?) class
    def gen_gcells(self):
        self.log.gen_gcells("start defining global cells")
        for gcl in self.db.mutyper.ldgcells:
            _id = self.bdr.gen_sym(str(gcl.mu_name))
            self.bdr.new_global_cell(_id, self.idmap[gcl._T])
            self.idmap[gcl] = _id

    def init_heap(self):
        self._create_heap_objects()

        # store in global cells
        for gcl in self.db.mutyper.ldgcells:
            gcl_id = self.idmap[gcl]
            hgcl = self.ctx.handle_from_global(gcl_id)
            href = self._objhdl_map[self.db.objtracer.gcells[gcl]]  # object root in gcell -> handle
            self.ctx.store(self._rmu.MuMemOrd.NOT_ATOMIC, hgcl, href)

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
                        ctx.store(self._rmu.MuMemOrd.NOT_ATOMIC, fld_iref, fld_hdl)

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
                    ctx.store(self._rmu.MuMemOrd.NOT_ATOMIC, elm_irf, elm_hdl)

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
                    ctx.store(self._rmu.MuMemOrd.NOT_ATOMIC, fld_iref, fld_hdl)


        for obj in objtracer.objs:
            _init_obj(obj)


class MuCSourceBundleGenerator(MuAPIBundleGenerator):
    _genc = True
    _newline = '\\n'

    def __init__(self, db):
        MuAPIBundleGenerator.__init__(self, db)
        _, self._rmu = get_rmu()

    def extras(self, bdlpath):
        with (bdlpath + '.c').open('w') as fp:
            self._rmu.get_global_apilogger().genc(fp)
