"""
Our own way of doing exception transform.
"""
from rpython.flowspace.model import c_last_exception, Constant, Block, Variable, FunctionGraph, Link, SpaceOperation
from rpython.rtyper.annlowlevel import MixLevelHelperAnnotator
from rpython.rtyper.llannotation import lltype_to_annotation
from rpython.rtyper.lltypesystem import lltype
from rpython.rtyper.lltypesystem.lltype import _ptr
from rpython.translator.backendopt.all import backend_optimizations
from rpython.mutyper.muts.muops import EXCEPT, DEST


class MuPyExcData(object):
    def __init__(self, exctype, excvalue):
        self.exc_type = exctype
        self.exc_value = excvalue


class ExceptionTransformer(object):
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

        def mupyexc_checktype(excdata, exctype):
            from rpython.rtyper.rclass import ll_issubclass
            return ll_issubclass(excdata.exc_type, exctype)     # Inspiration from translator/exceptiontransform.py

        def mupyexc_getvalue(excdata):
            return excdata.exc_value

        def mupyexc_gettype(excdata):
            return excdata.exc_type

        def mupyexc_printexctype(excdata):
            # msg_1 = "Error: Caught "
            # exc_type = llop.getinteriorfield(excdata, 'exc_type')
            # tn = llop.getinteriorfield(excdata.exc_type, 'name')
            # tn = excdata.exc_type.name
            # msg_2 = "at top level."
            # print msg_1 + tn + msg_2
            print "MuPy: Caught exception at top level."

        self.mupyexc_checktype = self.build_func(
            "_mupyexc_checktype",
            mupyexc_checktype,
            [self.ptr_excdata_llt, self.exctype_llt],
            lltype.Bool)

        self.mupyexc_getvalue = self.build_func(
            "_mupyexc_getvalue",
            mupyexc_getvalue,
            [self.ptr_excdata_llt],
            exc_val_llt)

        self.mupyexc_gettype = self.build_func(
            "_mupyexc_gettype",
            mupyexc_gettype,
            [self.ptr_excdata_llt],
            exc_type_llt)

        self.mupyexc_printexctype = self.build_func(
            "_mupyexc_printexctype",
            mupyexc_printexctype,
            [self.ptr_excdata_llt],
            lltype.Void)

        self.mlha.finish()

        self.helpergraphs = self.get_helpergraphs()
        backend_optimizations(translator, self.helpergraphs)
        translator.graphs.extend(self.helpergraphs)
        self.graphs = translator.graphs
        self._curg = None    # Current graph being processed

    def transform_all(self):
        for g in self.graphs:
            self.exctran(g)

    def linktran(self):
        """
        Transform the links.
        - wrap the exceptional llexitcases into a Constant
        - if a link needs attention (targets a raise block, or the block exitswitch is c_last_exception,
            check and see if the args needs to be packed into a MuPyExcData struct.
        - adds packing code to links whose arguments are non-'last_exc_...' Variables.

        :param g: rpython.flowspace.model.FunctionGraph
        :return: None
        """
        g = self._curg

        def exceptional_link(lnk, blk):
            return lnk.target is g.exceptblock or blk.exitswitch is c_last_exception

        for blk in g.iterblocks():
            for lnk in blk.exits:
                if exceptional_link(lnk, blk):
                    if len(lnk.args) == 1:
                        arg = lnk.args[0]
                        if isinstance(arg, Variable) and 'last_exc_value' in arg.name:
                            # This is the 'except ... as e' case.
                            # It should only has last_exc_value
                            # Set to the magic exception value which will be processed later on
                            lnk.args = [self.magicc_excvalue]
                    elif len(lnk.args) == 2 and \
                            isinstance(lnk.args[0], Variable) and isinstance(lnk.args[1], Variable) and \
                            'last_exception' in lnk.args[0].name and 'last_exc_value' in lnk.args[1].name:
                        lnk.args = [self.magicc_excdata]

    def get_pack_ops(self, var_type, var_value, blk):
        """
        Append the operation list of the block with operations that
        pack the exception type and value variables into
        a newly created MuPyExcData variable.
        """
        excdata = Variable('excdata')
        excdata.concretetype = self.ptr_excdata_llt
        ops = []
        ops.append(SpaceOperation('malloc',
                                  [Constant(self.ptr_excdata_llt.TO, lltype.Void), Constant({'flavor': 'gc'}, lltype.Void)],
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

    def exctran(self, g):
        """
        Perform exception transform on graph.

        :param g: rpython.flowspace.model.FunctionGraph
        :return: None
        """
        # In the raise block,
        # - pack the exception type and value,
        # - mu_throw it
        excblk = g.exceptblock
        excblk.operations, excdata = self.get_pack_ops(excblk.inputargs[0], excblk.inputargs[1], excblk)
        dummy_var = Variable()
        dummy_var.concretetype = lltype.Void
        excblk.operations.append(SpaceOperation('mu_throw', [excdata], dummy_var))

        self._curg = g

        # Transform the links
        self.linktran()

        g.mu_unpackblock = self.create_unpack_block()

        # create catch and compare blocks for blocks that have more than 2 exits,
        # and asserts that c_last_exception has to be the exitswitch
        blks = [b for b in g.iterblocks()]
        for blk in blks:
            if blk.exitswitch is c_last_exception:
                self.catch_and_compare(blk)

        # from rpython.translator.mu.tools.textdisp import _print_graph
        # _print_graph(g)

    def build_func(self, name, fnc, arg_ts, ret_t, **kwds):
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

    def create_link(self, src_blk, dst_blk, args, exitcase=None):
        lnk = Link(args, dst_blk)
        lnk.prevblock = src_blk
        lnk.exitcase = exitcase
        return lnk

    def catch_and_compare(self, blk):
        """
        Create blocks to catch the exception and
        compare it with the desired type

        :param blk: The block that has more than 2 exits, with c_last_exception being the exitswitch.
        :param g: The graph that the block belongs to.
        :return: None
        """
        def create_catch_block():
            blk_catch = Block([])
            blk_catch.operations = []

            excobjptr = Variable("excobjptr")
            excobjptr.concretetype = lltype.Ptr(lltype.OpaqueType('_Void'))
            blk_catch.mu_excparam = excobjptr

            excdataptr = Variable("excdataptr")
            excdataptr.concretetype = self.ptr_excdata_llt
            blk_catch.operations.append(SpaceOperation('cast_pointer', [excobjptr], excdataptr))

            return blk_catch, excdataptr

        if len(blk.exits) > 2:
            lnks = blk.exits
            blk_catch, excdataptr = create_catch_block()
            blk.exits = (lnks[0], self.create_link(blk, blk_catch, []))  # Replace the output link
            blk.raising_op.mu_exc = EXCEPT(DEST.from_link(lnks[0]), DEST.from_link(blk.exits[1]))
            chain = self.create_compare_blocks(lnks[1:])
            blk_catch.exits = (self.create_link(blk_catch, chain,
                                                [excdataptr, self.wrap_llexitcase(lnks[1].llexitcase)]), )
        else:
            assert len(blk.exits) == 2
            # An interesting case where there are only 1 definite exception case.
            l = blk.exits[1]
            if len(l.args) == 1 and (l.args[0] is self.magicc_excdata or l.args[0] is self.magicc_excvalue):
                blk_catch, excdataptr = create_catch_block()

                # Link them together
                blk_catch.exits = (l, )
                l.prevblock = blk_catch
                blk.exits = (blk.exits[0], self.create_link(blk, blk_catch, []))
                blk.raising_op.mu_exc = EXCEPT(DEST.from_link(blk.exits[0]), DEST.from_link(blk.exits[1]))

                # process args
                if l.args[0] is self.magicc_excdata:
                    l.args[0] = excdataptr
                else:
                    excval = Variable('excval')
                    excval.concretetype = self.excval_llt
                    blk_catch.operations.append(
                        SpaceOperation('direct_call',
                                       [self.mupyexc_getvalue, excdataptr],
                                       excval))
                    l.args[0] = excval
            else:
                # In such cases, ignore the checking; just catch the exception yet not doing anything with it.
                # An example of this is in rstr.ll_join_strs,
                # and the operation that throws an exception is int_add_nonneg_ovf
                # (which I'm not sure why it's not converted into a call).
                blk_catch = blk.exits[1].target
                excobjptr = Variable("excobjptr")
                excobjptr.concretetype = lltype.Ptr(lltype.OpaqueType('_Void'))
                blk_catch.mu_excparam = excobjptr
                blk.raising_op.mu_exc = EXCEPT(DEST.from_link(blk.exits[0]), DEST.from_link(blk.exits[1]))

    def create_compare_blocks(self, lnks):
        """
        For each link, create a compare block.
        The block should contain:
        - A call to mupyexc_checktype operation,
        - conditional branching based on the result
            - successful, then to what the original destination of the link
            - unsuccessful, then keep comparing and go to the next block.

        The input arguments for these comparison blocks are:
        - excdataptr
        - the exception type string

        :param lnks: The original links
        :return: the head of the compare block chain.
        """
        if len(lnks) == 1:
            lnk = lnks[0]
            if lnk.target is self._curg.exceptblock and lnk.args[0] is self.magicc_excdata:
                return self._curg.mu_unpackblock
            return None     # No need to add extra blocks

        # Create the compare block
        # Varaibles for the inputargs
        excdataptr = Variable('excdataptr')
        excdataptr.concretetype = self.ptr_excdata_llt
        typeobj = Variable('typeobj')
        typeobj.concretetype = self.exctype_llt

        blk = Block([excdataptr, typeobj])

        # Compare block operations
        cmpres = Variable("cmpres")
        cmpres.concretetype = lltype.Bool
        blk.operations.append(
            SpaceOperation('direct_call',
                           [self.mupyexc_checktype, excdataptr, typeobj],
                           cmpres))
        blk.exitswitch = cmpres

        lnk = lnks[0]   # Take out the head
        chain = self.create_compare_blocks(lnks[1:])    # Create chain for the rest
        lnk.prevblock = blk

        excval = None

        if lnk.target is self._curg.exceptblock:
            if len(lnk.args) == 1 and lnk.args[0] is self.magicc_excdata:
                lnk.target = self._curg.mu_unpackblock

        elif len(lnk.args) == 1 and lnk.args[0] is self.magicc_excvalue:
            # Handle the case there it attempts to pass the last caught exception value
            # Add a call to retrieve the value
            excval = Variable('excval')
            excval.concretetype = self.excval_llt
            blk.operations.append(
                SpaceOperation('direct_call',
                               [self.mupyexc_getvalue, excdataptr],
                               excval))
            lnk.args[0] = excval

        lnk.exitcase = True
        if chain:
            if chain is self._curg.mu_unpackblock:
                blk.exits = (self.create_link(blk, chain, [excdataptr], False), lnk)
            else:
                blk.exits = (self.create_link(blk, chain, [excdataptr, self.wrap_llexitcase(lnks[1].llexitcase)], False), lnk)
        else:
            l = lnks[1]
            l.prevblock = blk
            if len(l.args) == 1 and l.args[0] is self.magicc_excvalue:
                op = blk.operations[-1]
                if op.opname == 'direct_call' and op.args[0] is self.mupyexc_getvalue:  # already retrieved the value
                    assert excval
                    l.args[0] = excval
            l.exitcase = False
            blk.exits = (l, lnk)

        return blk

    def create_unpack_block(self):
        """
        Create an unpack block that unpacks the MuPyExcData structure,
        and links to the exceptblock of current graph.
        """
        excdata = Variable('excdata')
        excdata.concretetype = self.ptr_excdata_llt
        blk = Block([excdata])
        blk.operations = []
        exc_t = Variable('exc_t')
        exc_t.concretetype = self.exctype_llt
        blk.operations.append(SpaceOperation('direct_call',
                                             [self.mupyexc_gettype, excdata], exc_t))
        exc_v = Variable('exc_v')
        exc_v.concretetype = self.excval_llt
        blk.operations.append(SpaceOperation('direct_call',
                                             [self.mupyexc_getvalue, excdata], exc_v))
        blk.exits = (self.create_link(blk, self._curg.exceptblock, [exc_t, exc_v]), )
        return blk

    def wrap_llexitcase(self, llexitcase):
        if llexitcase and isinstance(llexitcase, _ptr) and llexitcase._TYPE == self.exctype_llt:
            llexitcase = Constant(llexitcase, llexitcase._TYPE)
        return llexitcase

    def get_helpergraphs(self):
        """
        :return: All the created graphs for exception transform.
        """
        graphs = [_get_graph(self.mupyexc_checktype),
                  _get_graph(self.mupyexc_getvalue),
                  _get_graph(self.mupyexc_gettype),
                  _get_graph(self.mupyexc_printexctype)]

        for graph in graphs[:3]:
            for blk in graph.iterblocks():
                for op in blk.operations:
                    if op.opname == 'direct_call':
                        g = _get_graph(op.args[0])
                        if g not in graphs:
                            graphs.append(g)

        return graphs

    # def gen_toplevel_excblock(self, muentrypoint, mutyper, gsymtbl):
    #     blk = MuBlock(muentrypoint, len(muentrypoint.blocks))
    #     ty = mutyper.typemapper.type_lookup("@refvoid")
    #     if ty:
    #         excobjptr = MuVariable('excobjptr', None, ty, muentrypoint)
    #         refexcobj = add_op(blk.operations, LANDINGPAD(excobjptr))
    #     else:
    #         refexcobj = add_op(blk.operations, LANDINGPAD(None, muentrypoint))
    #
    #     refexcdata = add_op(blk.operations, REFCAST(refexcobj.mutype,
    #                                                 mutyper.typemapper.ll2mu(self.ptr_excdata_llt),
    #                                                 refexcobj))
    #     add_op(blk.operations, CALL(gsymtbl.fncgraph_dic[_get_graph(self.mupyexc_printexctype)], [refexcdata]))
    #     return blk


def _get_graph(fc):
    return fc.value._obj.graph
