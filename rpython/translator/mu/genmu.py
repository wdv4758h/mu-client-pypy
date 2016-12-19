from rpython.config.translationoption import get_translation_config
from rpython.tool.ansi_print import AnsiLogger
from rpython.tool.ansi_mandelbrot import Driver
from rpython.translator.mu import mutype
import py

__mdb = Driver()


def get_rmu():
    from rpython.config.translationoption import get_translation_config
    from rpython.rlib import rmu
    config = get_translation_config()
    mod_name = config.translation.mu.impl + ('_c' if config.translation.mu.codegen == 'c' else '')
    return getattr(rmu, mod_name)


class MuBundleGen:
    def __init__(self, db):
        # type: (rpython.translator.mu.database.MuDatabase) -> None
        self.db = db
        self.idmap = {}
        self.rmu = get_rmu()
        self.mu_config = get_translation_config().translation.mu
        # self.mu = self.rmu.MuVM(self.mu_config.vmargs)
        self.mu = self.rmu.MuVM('dumpBundle=True')
        self.ctx = self.mu.new_context()
        self.bdr = self.ctx.new_ir_builder()
        self.objhdlmap = {}     # used in heap initialisation; NOTE: referent -> handle (not reference)
        self.log = AnsiLogger('MuBundleGen')

    def build_and_load_bundle(self):
        # generate all symbols first
        self.idmap = self.db.mu_name_map.copy()
        for entity in self.idmap:
            _name = self.idmap[entity]
            _id = self.bdr.gen_sym(_name)
            self.idmap[entity] = _id   # drop the name

        self.gen_types()
        self.gen_consts()
        self.gen_gcells()
        self.gen_graphs()
        self.bdr.load()

    def gen_boot_image(self, targetname):
        self.build_and_load_bundle()
        self.init_heap()

        if self.mu_config.testjit:
            from rpython.translator.platform import platform
            libname = targetname + '.' + platform.so_ext
            self.mu.compile_to_sharedlib(libname, [])
        else:
            hmain = self.ctx.handle_from_func(self._id_of(self.db.tlc.entry_point_graph))
            topdefs = []
            topdefs.extend(self._ids_of(self.db.types))
            topdefs.extend(self._ids_of(self.db.consts))
            topdefs.extend(self._ids_of(self.db.extern_fncs))
            topdefs.extend(self._ids_of(self.db.graphs))
            self.ctx.make_boot_image(topdefs, hmain,
                                     self.rmu.null(self.rmu.MuStackRefValue),
                                     self.rmu.null(self.rmu.MuRefValue),
                                     [], [], [], [], targetname)

        if hasattr(self.mu, 'close'):
            self.mu.close()

        if self.mu_config.codegen == 'api':
            if self.mu_config.impl == 'ref':
                if self.db.libsupport_path:
                    from mar import mu_meta_set
                    mu_meta_set(str(targetname), extra_libraries=self.db.libsupport_path.strpath)
        else:
            with py.path.local(targetname + '.c').open('w') as fp:
                self.rmu.get_global_apilogger().genc(fp)

    def gen_types(self):
        for T in self.db.types:
            _id = self._id_of(T)
            if isinstance(T, mutype.MuIntType):
                self.bdr.new_type_int(_id, T.BITS)
            elif T == mutype.MU_FLOAT:
                self.bdr.new_type_float(_id)
            elif T == mutype.MU_DOUBLE:
                self.bdr.new_type_double(_id)
            elif T == mutype.MU_VOID:
                self.bdr.new_type_void(_id)
            elif isinstance(T, mutype.MuStruct):
                self.bdr.new_type_struct(_id, self._ids_of(T._field_types()))
            elif isinstance(T, mutype.MuHybrid):
                self.bdr.new_type_hybrid(_id, self._ids_of(T._fixed_field_types()),
                                         self._id_of(T._var_field_type()))
            elif isinstance(T, mutype.MuArray):
                self.bdr.new_type_array(_id, self._id_of(T.OF), T.length)
            elif isinstance(T, mutype.MuFuncSig):
                self.bdr.new_funcsig(_id, self._ids_of(T.ARGS), self._ids_of(T.RESULTS))
            elif isinstance(T, mutype.MuFuncRef):
                self.bdr.new_type_funcref(_id, self._id_of(T.Sig))
            elif isinstance(T, mutype.MuUFuncPtr):
                self.bdr.new_type_ufuncptr(_id, self._id_of(T.Sig))
            elif isinstance(T, mutype.MuRef):
                self.bdr.new_type_ref(_id, self._id_of(T.TO))
            elif isinstance(T, mutype.MuIRef):
                self.bdr.new_type_iref(_id, self._id_of(T.TO))
            elif isinstance(T, mutype.MuUPtr):
                self.bdr.new_type_uptr(_id, self._id_of(T.TO))

    def gen_consts(self):
        for c in self.db.consts:
            T = c.concretetype
            v = c.value
            _id = self._id_of(c)
            _id_T = self._id_of(T)
            if isinstance(T, mutype.MuIntType):
                if not isinstance(T, mutype.MuBigIntType):
                    self.bdr.new_const_int(_id, _id_T, v)
                else:
                    self.bdr.new_const_int_ex(_id, _id_T, v.get_uint64s())
            elif T == mutype.MU_FLOAT:
                self.bdr.new_const_float(_id, _id_T, float(v))
            elif T == mutype.MU_DOUBLE:
                self.bdr.new_const_double(_id, _id_T, float(v))
            elif isinstance(T, mutype.MuReferenceType):
                assert v._is_null()
                self.bdr.new_const_null(_id, _id_T)

        for c in self.db.extern_fncs:
            self.bdr.new_const_extern(self._id_of(c), self._id_of(c.concretetype), c.value._name)

    def gen_gcells(self):
        for gcl in self.db.gcells:
            self.bdr.new_global_cell(self._id_of(gcl), self._id_of(gcl.concretetype.TO))

    def gen_graphs(self):
        for frc in self.db.funcref_consts:
            self.idmap[frc] = self.idmap[frc.value.graph]

        for g in self.db.graphs:
            self.log.gen_graphs("generating function %s" % g)
            self.bdr.new_func(self._id_of(g), self._id_of(g.sig))
            self.bdr.new_func_ver(self.bdr.gen_sym('@' + g.name + '_v1'),
                                  self._id_of(g), self._ids_of(g.iterblocks()))

            for blk in g.iterblocks():
                op_ids = []
                for op in filter(lambda op: op.opname.startswith('mu_'), blk.operations):
                    _id = self.bdr.gen_sym()
                    op_ids.append(_id)
                    mtd = getattr(self, '_genop_' + op.opname)
                    mtd(op, _id)
                self.bdr.new_bb(self._id_of(blk),
                                self._ids_of(blk.inputargs),
                                self._ids_of(map(lambda a: a.concretetype, blk.inputargs)),
                                self._id_of(blk.mu_excparam) if blk.mu_excparam else self.rmu.MU_NO_ID,
                                op_ids)

    def _genop_mu_binop(self, op, op_id):
        metainfo = op.args[-1].value
        if hasattr(metainfo, 'status'):
            self.bdr.new_binop_with_status(op_id, self._id_of(op.result),
                                           self._ids_of(metainfo['status'][1]),
                                           getattr(self.rmu.MuBinOptr, op.args[0].value),
                                           getattr(self.rmu.MuBinOpStatus, metainfo['status'][0]),
                                           self._id_of(op.args[1].concretetype),
                                           self._id_of(op.args[1]), self._id_of(op.args[2]))
        else:
            self.bdr.new_binop(op_id, self._id_of(op.result),
                               getattr(self.rmu.MuBinOptr, op.args[0].value),
                               self._id_of(op.args[1].concretetype),
                               self._id_of(op.args[1]), self._id_of(op.args[2]))

    def _genop_mu_cmpop(self, op, op_id):
        self.bdr.new_cmp(op_id, self._id_of(op.result),
                         getattr(self.rmu.MuCmpOptr, op.args[0].value),
                         self._id_of(op.args[1].concretetype),
                         self._id_of(op.args[1]), self._id_of(op.args[2]))

    def _genop_mu_convop(self, op, op_id):
        self.bdr.new_conv(op_id, self._id_of(op.result),
                          getattr(self.rmu.MuConvOptr, op.args[0].value),
                          self._id_of(op.args[2].concretetype),
                          self._id_of(op.args[1].value),
                          self._id_of(op.args[2]))

    def _genop_mu_select(self, op, op_id):
        self.bdr.new_select(op_id, self._id_of(op.result),
                            self._id_of(op.args[0].concretetype),
                            self._id_of(op.args[1].concretetype),
                            self._id_of(op.args[0]),
                            self._id_of(op.args[1]), self._id_of(op.args[2]))

    def _genop_mu_branch(self, op, op_id):
        dst = self.bdr.gen_sym()
        self.bdr.new_dest_clause(dst, self._id_of(op.args[0].value.target),
                                 self._ids_of(op.args[0].value.args))
        self.bdr.new_branch(op_id, dst)

    def _genop_mu_branch2(self, op, op_id):
        dst_t = self.bdr.gen_sym()
        dst_f = self.bdr.gen_sym()
        lnk_t = op.args[1].value
        lnk_f = op.args[2].value
        self.bdr.new_dest_clause(dst_t, self._id_of(lnk_t.target), self._ids_of(lnk_t.args))
        self.bdr.new_dest_clause(dst_f, self._id_of(lnk_f.target), self._ids_of(lnk_f.args))
        self.bdr.new_branch2(op_id, self._id_of(op.args[0]), dst_t, dst_f)

    def _genop_mu_switch(self, op, op_id):
        dst_dfl = self.bdr.gen_sym()
        lnk_dfl = op.args[1].value
        self.bdr.new_dest_clause(dst_dfl, self._id_of(lnk_dfl.target), self._ids_of(lnk_dfl.args))
        case_lnks = op.args[2:]
        dst_ids = []
        for lnk_c in case_lnks:
            lnk = lnk_c.value
            _id = self.bdr.gen_sym()
            dst_ids.append(_id)
            self.bdr.new_dest_clause(_id, self._id_of(lnk.target), self._ids_of(lnk.args))

        self.bdr.new_switch(op_id, self._id_of(op.args[0].concretetype), self._id_of(op.args[0]),
                            dst_dfl,
                            self._ids_of(map(lambda l_c: l_c.value.exitcase, case_lnks)),
                            dst_ids)

    def _genop_mu_call(self, op, op_id):
        metainfo = op.args[-1].value
        if 'excclause' in metainfo:
            lnk_n, lnk_e = metainfo['excclause']
            dst_n = self.bdr.gen_sym()
            dst_e = self.bdr.gen_sym()
            exc = self.bdr.gen_sym()
            self.bdr.new_dest_clause(dst_n, self._id_of(lnk_n.target), self._ids_of(lnk_n.args))
            self.bdr.new_dest_clause(dst_e, self._id_of(lnk_e.target), self._ids_of(lnk_e.args))
            self.bdr.new_exc_clause(exc, dst_n, dst_e)
        else:
            exc = self.rmu.MU_NO_ID
        self.bdr.new_call(op_id, [self._id_of(op.result)],
                          self._id_of(op.args[0].concretetype.Sig), self._id_of(op.args[0]),
                          self._ids_of(op.args[1:-1]), exc)

    def _genop_mu_ret(self, op, op_id):
        self.bdr.new_ret(op_id, self._ids_of(op.args))

    def _genop_mu_throw(self, op, op_id):
        self.bdr.new_throw(op_id, self._id_of(op.args[0]))

    def _genop_mu_new(self, op, op_id):
        self.bdr.new_new(op_id, self._id_of(op.result), self._id_of(op.args[0].value))

    def _genop_mu_newhybrid(self, op, op_id):
        self.bdr.new_newhybrid(op_id, self._id_of(op.result),
                               self._id_of(op.args[0].value),
                               self._id_of(op.args[1].concretetype),
                               self._id_of(op.args[1]))

    def _genop_mu_getiref(self, op, op_id):
        self.bdr.new_getiref(op_id, self._id_of(op.result),
                             self._id_of(op.args[0].concretetype.TO), self._id_of(op.args[0]))

    def _genop_mu_getfieldiref(self, op, op_id):
        self.bdr.new_getfieldiref(op_id, self._id_of(op.result),
                                  isinstance(op.args[0].concretetype, mutype.MuUPtr),
                                  self._id_of(op.args[0].concretetype.TO),
                                  op.args[0].concretetype.TO._index_of(op.args[1].value),
                                  self._id_of(op.args[0]))

    def _genop_mu_getelemiref(self, op, op_id):
        self.bdr.new_getelemiref(op_id, self._id_of(op.result),
                                 isinstance(op.args[0].concretetype, mutype.MuUPtr),
                                 self._id_of(op.args[0].concretetype.TO),
                                 self._id_of(op.args[1].concretetype),
                                 self._id_of(op.args[0]), self._id_of(op.args[1]))

    def _genop_mu_shiftiref(self, op, op_id):
        self.bdr.new_shiftiref(op_id, self._id_of(op.result),
                               isinstance(op.args[0].concretetype, mutype.MuUPtr),
                               self._id_of(op.args[0].concretetype.TO),
                               self._id_of(op.args[1].concretetype),
                               self._id_of(op.args[0]), self._id_of(op.args[1]))

    def _genop_mu_getvarpartiref(self, op, op_id):
        self.bdr.new_getvarpartiref(op_id, self._id_of(op.result),
                                    isinstance(op.args[0].concretetype, mutype.MuUPtr),
                                    self._id_of(op.args[0].concretetype.TO),
                                    self._id_of(op.args[0]))

    def _genop_mu_load(self, op, op_id):
        self.bdr.new_load(op_id, self._id_of(op.result),
                          isinstance(op.args[0].concretetype, mutype.MuUPtr),
                          getattr(self.rmu.MuMemOrd, op.args[-1].value['memord']),
                          self._id_of(op.args[0].concretetype.TO),
                          self._id_of(op.args[0]))

    def _genop_mu_store(self, op, op_id):
        self.bdr.new_store(op_id,
                           isinstance(op.args[0].concretetype, mutype.MuUPtr),
                           getattr(self.rmu.MuMemOrd, op.args[-1].value['memord']),
                           self._id_of(op.args[0].concretetype.TO),
                           self._id_of(op.args[0]),
                           self._id_of(op.args[1]))

    def _genop_mu_ccall(self, op, op_id):
        self.bdr.new_ccall(op_id, [self._id_of(op.result)],
                           getattr(self.rmu.MuCallConv, op.args[-1].value['callconv']),
                           self._id_of(op.args[0].concretetype),
                           self._id_of(op.args[0].concretetype.Sig),
                           self._id_of(op.args[0]),
                           self._ids_of(op.args[1:-1]))

    def _genop_mu_comminst(self, op, op_id):
        metainfo = op.args[-1].value
        if 'flags' in metainfo:
            raise NotImplementedError
        else:
            flags = []
        types = self._ids_of(metainfo['types']) if 'types' in metainfo else []
        sigs = self._ids_of(metainfo['sigs']) if 'sigs' in metainfo else []
        self.bdr.new_comminst(op_id, [self._id_of(op.result)],
                              getattr(self.rmu.MuCommInst, self.args[0].value),
                              flags, types, sigs,
                              self._ids_of(op.args[1:-1]))

    def _id_of(self, entity):
        return self.idmap[entity]

    def _ids_of(self, lst_entity):
        return map(self.idmap.get, lst_entity)

    def init_heap(self):
        pass
