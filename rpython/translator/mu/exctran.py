"""
Our own way of doing exception transform.
"""
from rpython.flowspace.model import c_last_exception, Constant, Block, Variable, FunctionGraph, Link, SpaceOperation
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

        def _collect_args(links):
            # Collect the 'normal' program arguments
            args = set()
            for lnk in links:
                for arg in lnk.args:
                    if not (isinstance(arg, Variable) and arg in (lnk.last_exception, lnk.last_exc_value)):
                        args.add(arg)
            return list(args)

        def _link(src_blk, dst_blk, args, exitcase=None):
            lnk = Link(args, dst_blk)
            lnk.prevblock = src_blk
            lnk.exitcase = exitcase
            return lnk

        def _has_excinfo_var(exclnk):
            return (isinstance(exclnk.last_exception, Variable) and exclnk.last_exception in exclnk.args) or \
                   (isinstance(exclnk.last_exc_value, Variable) and exclnk.last_exc_value in exclnk.args)

        def _create_compare_blocks(lnks, cases, inargs):
            """
            For each link, create a compare block.
            The block should contain:
            - A call to mupyexc_checktype operation,
            - conditional branching based on the result
                - successful, then to what the original destination of the link
                - unsuccessful, then keep comparing and go to the next block.

            The input arguments for these comparison blocks are:
            - thrown exception type variable
            - thrown exception value variable
            - exception type to check against
            - other arguments

            :param lnks: The original links
            :param inargs: input args for the compare block
            :return: the head of the compare block chain.
            """
            vexc_t, vexc_v = inargs[:2]
            case = cases[0]

            def _create_compare_block():
                # Create the compare block
                # Varaibles for the inputargs
                blk = Block(inargs)
                ops = []

                cmpres = Variable("cmpres")
                cmpres.concretetype = lltype.Bool
                ops.append(SpaceOperation('direct_call',
                                          [self.mupyexc_checktype, vexc_t, case],
                                          cmpres))
                blk.operations = tuple(ops)
                blk.exitswitch = cmpres
                return blk

            cmpblk = _create_compare_block()
            if len(lnks) == 2:
                lnks[0].prevblock = cmpblk
                lnks[1].prevblock = cmpblk
                cmpblk.exits = (lnks[1], lnks[0])
            else:
                _args = [vexc_t, vexc_v] + list(set(inargs[2:]) & set(_collect_args(lnks[1:])))
                chain = _create_compare_blocks(lnks[1:], cases[1:], _args)
                cmpblk.exits = (_link(cmpblk, chain, _args), lnks[0])

            return cmpblk

        if len(excblk.exits) > 2:
            lnks = excblk.exits[1:]
            args = _collect_args(lnks)
            catblk, var_exc_t, var_exc_v = _create_catch_block(args)
            excblk.exits = (excblk.exits[0], _link(excblk, catblk, args))
            args = [var_exc_t, var_exc_v] + args

            # replace the exception info vars with the unpacked vars
            for l in lnks:
                if l.last_exception in l.args:
                    l.args[l.args.index(l.last_exception)] = var_exc_t
                if l.last_exc_value in l.args:
                    l.args[l.args.index(l.last_exc_value)] = var_exc_v

            # wrap the llexitcases
            cases = []
            for l in lnks:
                assert isinstance(l.llexitcase, _ptr)
                cases.append(Constant(l.llexitcase, l.llexitcase._TYPE))

            cmp_chain = _create_compare_blocks(lnks, cases, args)
            catblk.exits = (_link(catblk, cmp_chain, args),)
        elif len(excblk.exits) == 2:
            exclnk = excblk.exits[1]
            if _has_excinfo_var(exclnk):
                # Exception info in args ->
                # needs to catch and unpack the exception data
                args = _collect_args([exclnk])
                catblk, var_exc_t, var_exc_v = _create_catch_block(args)
                excblk.exits = (excblk.exits[0], _link(excblk, catblk, args))

                # unpack in the catch block
                # replace the variable in args in exit links
                if exclnk.last_exception in exclnk.args:
                    exclnk.args[exclnk.args.index(exclnk.last_exception)] = var_exc_t
                if exclnk.last_exc_value in exclnk.args:
                    exclnk.args[exclnk.args.index(exclnk.last_exc_value)] = var_exc_v

                # set the catch block exits
                exclnk.prevblock = catblk
                catblk.exits = (exclnk, )
            else:   # exception information is not used. -> ignore the raised exception
                pass

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
