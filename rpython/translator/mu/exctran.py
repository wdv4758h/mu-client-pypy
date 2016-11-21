"""
Our own way of doing exception transform.
"""
from rpython.flowspace.model import c_last_exception, Constant, Block, Variable, Link, SpaceOperation
from rpython.rtyper.annlowlevel import MixLevelHelperAnnotator
from rpython.rtyper.llannotation import lltype_to_annotation
from rpython.rtyper.lltypesystem import lltype
from rpython.rtyper.lltypesystem.lltype import _ptr
from rpython.translator.backendopt.all import backend_optimizations


class MuExceptionTransformer:
    def __init__(self, translator):
        self.rtyper = translator.rtyper
        self.mlha = MixLevelHelperAnnotator(self.rtyper)

        excdata = self.rtyper.exceptiondata
        exc_type_llt = excdata.lltype_of_exception_type
        exc_val_llt = excdata.lltype_of_exception_value
        self.exctype_llt = exc_type_llt
        self.excval_llt = exc_val_llt

        self.ptr_excdata_llt = lltype.Ptr(
            lltype.GcStruct('MuPyExcData',
                            ('exc_type', exc_type_llt),
                            ('exc_value', exc_val_llt)))

        self.magicc_excdata = Variable('magicc_excdata')
        self.magicc_excvalue = Variable('magicc_excvalue')

        def mupyexc_checktype(exc_t, exctype):
            from rpython.rtyper.rclass import ll_issubclass
            return ll_issubclass(exc_t, exctype)  # Inspiration from translator/exceptiontransform.py

        def mupyexc_getvalue(excdata):
            return excdata.exc_value

        def mupyexc_gettype(excdata):
            return excdata.exc_type

        def _build_func(name, fnc, arg_ts, ret_t, **kwds):
            """
            Build a FunctionGraph out of RPython code.
            Taken from rpython.translator.exceptiontransform.py
            """
            fnc_l2a = lltype_to_annotation
            graph = self.mlha.getgraph(fnc, map(fnc_l2a, arg_ts), fnc_l2a(ret_t))
            func_t = lltype.FuncType(arg_ts, ret_t)
            fnc_ptr = lltype.functionptr(func_t, name, graph=graph,
                                         exception_policy='exc_helper', **kwds)

            return Constant(fnc_ptr, lltype.Ptr(func_t))

        self.mupyexc_checktype = _build_func(
            "_mupyexc_checktype",
            mupyexc_checktype,
            [self.exctype_llt, self.exctype_llt],
            lltype.Bool)

        self.mupyexc_getvalue = _build_func(
            "_mupyexc_getvalue",
            mupyexc_getvalue,
            [self.ptr_excdata_llt],
            exc_val_llt)

        self.mupyexc_gettype = _build_func(
            "_mupyexc_gettype",
            mupyexc_gettype,
            [self.ptr_excdata_llt],
            exc_type_llt)

        self.mlha.finish()

        def _get_helpergraphs():
            """
            :return: All the created graphs for exception transform.
            """
            _get_graph = lambda fc: fc.value._obj.graph
            graphs = [_get_graph(self.mupyexc_checktype),
                      _get_graph(self.mupyexc_getvalue),
                      _get_graph(self.mupyexc_gettype)]

            for graph in graphs[:3]:
                for blk in graph.iterblocks():
                    for op in blk.operations:
                        if op.opname == 'direct_call':
                            g = _get_graph(op.args[0])
                            if g not in graphs:
                                graphs.append(g)

            return graphs

        self.helpergraphs = _get_helpergraphs()
        backend_optimizations(translator, self.helpergraphs)
        # translator.graphs.extend(self.helpergraphs)
        self.graphs = translator.graphs

    def transform_all(self):
        for g in self.graphs:
            self.exctran(g)

    def exctran(self, g):
        # In the raise block,
        # - pack the exception type and value,
        # - mu_throw it
        excblk = g.exceptblock
        excblk.operations, excdata = self._get_pack_ops(excblk.inputargs[0], excblk.inputargs[1])
        dummy_var = Variable()
        dummy_var.concretetype = lltype.Void
        excblk.operations.append(SpaceOperation('mu_throw', [excdata], dummy_var))

        # Transform each block that raises exception
        for blk in g.iterblocks():
            if blk.exitswitch is c_last_exception:
                self.exctran_block(blk)

    def exctran_block(self, excblk):
        """
        An example of what this should do:
                               +--------+
                               | excblk |
                               +--------+
                                 |  |  |      [last_exception, last_exc_value]
                 +---------------+  |  +--------------------+
                 | [a, b]           |                       |
                 |                  |[c, d, last_exc_value] |
              +--v---+       +------v------+         +------v-------+
              |[a, b]|       |[c, d, exc_v]|         |[exc_t, exc_v]|
              |      |       |             |         |              |
              | blk0 |       |    blk1     |         |     blk2     |
              +------+       +-------------+         +--------------+

                                    ++
                                    ||
                                    ||
                                    ||
                                    ||
                                    ||
                                    ||
                                    ||
                                    vv

                                +--------+
                                | excblk |
                                +--------+
                                  |  |
                  +---------------+  |[c, d]
                  |    [a, b]        |
                  |                  |
               +--v---+       +------v------+
               |[a, b]|       |   [c, d]    |
               |      |       |             |
               | blk0 |       |   catblk    |
               +------+       +-------------+
                                     |
                                     |[exc_t, exc_v, c, d]
                                     |
                                     v
                          +--------------------+
                          |[exc_t, exc_v, c, d]|
                          |       cmpblk       |
                          | cmp_res = call(...)|
                          |                    |
                          |exitswitch: cmp_res |
                          +--------------------+
                               |       |
                    +----------+       +---------+ [exc_t, exc_v]
                    |  [c, d, exc_v]             |
                    |                            |
             +------v------+              +------v-------+
             |[c, d, exc_v]|              |[exc_t, exc_v]|
             |             |              |              |
             |    blk1     |              |     blk2     |
             +-------------+              +--------------+

        @param excblk:
        @return:
        """
        def _create_catch_block(args):
            blk_catch = Block(args)
            ops = []
            excobjptr = Variable("excobjptr")
            excobjptr.concretetype = lltype.Ptr(lltype.GcOpaqueType('_Void'))
            blk_catch.mu_excparam = excobjptr

            excdataptr = Variable("excdataptr")
            excdataptr.concretetype = self.ptr_excdata_llt
            ops.append(SpaceOperation('cast_pointer', [Constant(self.ptr_excdata_llt, lltype.Void), excobjptr], excdataptr))

            # Unpack it here
            exc_t = Variable('exc_t')
            exc_t.concretetype = self.exctype_llt
            ops.append(SpaceOperation('direct_call', [self.mupyexc_gettype, excdataptr], exc_t))

            exc_v = Variable('exc_v')
            exc_v.concretetype = self.excval_llt
            ops.append(SpaceOperation('direct_call', [self.mupyexc_getvalue, excdataptr], exc_v))
            blk_catch.operations = tuple(ops)
            return blk_catch, exc_t, exc_v

        def _get_local_varmap(inlnk_args):
            varmap = {}
            for a in filter(lambda a: isinstance(a, Variable), inlnk_args):
                v = Variable(a._name[:-1])
                v.concretetype = a.concretetype
                varmap[a] = v
            return varmap
        def _localise_args(args, varmap):
            return [varmap[a] if isinstance(a, Variable) else a for a in args]

        def _process_exception(exclnks, cases, inlnk_args):
            # NOTE: this function returns a link rather than block
            if len(exclnks) == 1:
                # directly return this link
                return exclnks[0]

            else: # otherwise, create a compare block
                # localise variables
                lvmap = _get_local_varmap(inlnk_args)
                inargs_cmpblk = _localise_args(inlnk_args, lvmap)
                for lnk in exclnks:
                    lnk.args = _localise_args(lnk.args, lvmap)
                # pickout things specific to this comparison
                vexc_t, vexc_v = inargs_cmpblk[:2]
                case = cases.pop(0)
                exclnk = exclnks.pop(0)

                cmpblk = Block(inargs_cmpblk)

                # add compare call to block
                cmpres = Variable("cmpres")
                cmpres.concretetype = lltype.Bool
                cmpblk.operations = (SpaceOperation('direct_call', [self.mupyexc_checktype, vexc_t, case], cmpres), )
                cmpblk.exitswitch = cmpres

                # recursively call on rest of the links
                norm_args = _collect_normal_args(exclnks)
                lnk_rest = _process_exception(exclnks, cases, norm_args)
                lnk_rest.prevblock = cmpblk
                cmpblk.exits = (lnk_rest, exclnk)

                # return a link to this comparison block
                return Link(inlnk_args, cmpblk)

        def _catch_and_process_exception(exclnks, cases, inlnk_args):
            # create catch block
            lvmap = _get_local_varmap(inlnk_args)
            inargs_catblk = _localise_args(inlnk_args, lvmap)
            catblk, vexc_t_catblk, vexc_v_catblk = _create_catch_block(inargs_catblk)

            # replace the exception info vars with the unpacked vars
            for l in exclnks:
                if isinstance(l.last_exception, Variable) and l.last_exception in l.args:
                    lvmap[l.last_exception] = vexc_t_catblk
                if isinstance(l.last_exc_value, Variable) and l.last_exc_value in l.args:
                    lvmap[l.last_exc_value] = vexc_v_catblk

            # localise all link arguments
            for lnk in exclnks:
                lnk.args = _localise_args(lnk.args, lvmap)

            lnk_args = [vexc_t_catblk, vexc_v_catblk] + inargs_catblk

            lnk_proc = _process_exception(exclnks, cases, lnk_args)
            lnk_proc.prevblock = catblk
            catblk.exits = (lnk_proc, )
            return catblk

        exclnks = list(excblk.exits[1:])
        if len(exclnks) == 1 and not _has_excinfo_var(exclnks[0]):
            # exception information is not used. -> ignore the raised exception
            return

        # need to create catch block
        # wrap the llexitcases
        cases = []
        for l in exclnks:
            assert isinstance(l.llexitcase, _ptr)
            cases.append(Constant(l.llexitcase, l.llexitcase._TYPE))
        norm_args = _collect_normal_args(exclnks)
        catblk = _catch_and_process_exception(exclnks, cases, norm_args)
        excblk.exits = (excblk.exits[0], _link(excblk, catblk, norm_args))

    def _get_pack_ops(self, var_type, var_value):
        """
        Return a list of operations that packs the exception type and value.
        :param var_type: Variable exc_type
        :param var_value: Variable exc_val
        :return: [SpaceOperation], Variable('excdata')
        """
        excdata = Variable('excdata')
        excdata.concretetype = self.ptr_excdata_llt
        ops = []
        ops.append(SpaceOperation('malloc',
                                  [Constant(self.ptr_excdata_llt.TO, lltype.Void),
                                   Constant({'flavor': 'gc'}, lltype.Void)],
                                  excdata))
        dummy_var = Variable()
        dummy_var.concretetype = lltype.Void
        ops.append(SpaceOperation('setfield',
                                  [excdata, Constant('exc_type', lltype.Void), var_type],
                                  dummy_var))
        dummy_var = Variable()
        dummy_var.concretetype = lltype.Void
        ops.append(SpaceOperation('setfield',
                                  [excdata, Constant('exc_value', lltype.Void), var_value],
                                  dummy_var))

        return ops, excdata


def _has_excinfo_var(exclnk):
    return (isinstance(exclnk.last_exception, Variable) and exclnk.last_exception in exclnk.args) or \
           (isinstance(exclnk.last_exc_value, Variable) and exclnk.last_exc_value in exclnk.args)

def _collect_normal_args(exclnks):
    norm_args = set()
    for lnk in exclnks:
        for arg in lnk.args:
            if not arg in (lnk.last_exception, lnk.last_exc_value):
                norm_args.add(arg)
    return list(norm_args)

def _link(src_blk, dst_blk, args, exitcase=None):
    lnk = Link(args, dst_blk)
    lnk.prevblock = src_blk
    lnk.exitcase = exitcase
    return lnk