"""
Our own way of doing exception transform.
"""
from rpython.flowspace.model import c_last_exception, Constant, Block, Variable, FunctionGraph, Link, SpaceOperation
from rpython.rtyper.annlowlevel import MixLevelHelperAnnotator
from rpython.rtyper.llannotation import lltype_to_annotation
from rpython.rtyper.lltypesystem import lltype
from rpython.rtyper.lltypesystem.lltype import _ptr
from rpython.mutyper.muts.muops import CALL, EXCEPT, DEST
from rpython.mutyper.ll2mu import _MuOpList
from rpython.translator.backendopt.all import backend_optimizations


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
            lltype.Struct('MuPyExcData',
                          ('exc_type', exc_type_llt),
                          ('exc_value', exc_val_llt)))

        self.magicc_excdata = Variable('magicc_excdata')
        self.magicc_excvalue = Variable('magicc_excvalue')

        def mupyexc_checktype(excdata, exctype):
            from rpython.rtyper.rclass import ll_issubclass
            return ll_issubclass(excdata.exc_type, exctype)     # Inspiration from translator/exceptiontransform.py

        def mupyexc_getvalue(excdata):
            return excdata.exc_value

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

        self.mlha.finish()

        self.helpergraphs = self.get_helpergraphs()
        backend_optimizations(translator, self.helpergraphs)

    def linktran(self, g):
        """
        Transform the links.
        - wrap the exceptional llexitcases into a Constant
        - if a link needs attention (targets a raise block, or the block exitswitch is c_last_exception,
            check and see if the args needs to be packed into a MuPyExcData struct.
        - adds packing code to links whose arguments are non-'last_exc_...' Variables.

        :param g: rpython.flowspace.model.FunctionGraph
        :return: None
        """

        def exceptional_link(lnk, blk):
            return lnk.target == g.exceptblock or blk.exitswitch == c_last_exception

        def wrap_llexitcase(lnk):
            if hasattr(lnk, 'llexitcase') and lnk.llexitcase and isinstance(lnk.llexitcase, _ptr) and lnk.llexitcase._TYPE == self.exctype_llt:
                lnk.llexitcase = Constant(lnk.llexitcase, lnk.llexitcase._TYPE)

        for blk in g.iterblocks():
            for lnk in blk.exits:
                if exceptional_link(lnk, blk):
                    wrap_llexitcase(lnk)
                    if len(lnk.args) == 1:
                        arg = lnk.args[0]
                        assert isinstance(arg, Variable)
                        if 'last_exc_value' in arg.name:
                            # This is the 'except ... as e' case.
                            # It should only has last_exc_value
                            # Set to the magic exception value which will be processed later on
                            lnk.args = [self.magicc_excvalue]
                    elif len(lnk.args) == 2:
                        if isinstance(lnk.args[0], Constant) and isinstance(lnk.args[1], Constant):
                            lnk.args = [self.pack_exccnst(lnk.args[0].value, lnk.args[1].value)]

                        elif isinstance(lnk.args[0], Variable) and isinstance(lnk.args[1], Variable):
                            if 'last_exception' in lnk.args[0].name and 'last_exc_value' in lnk.args[1].name:
                                lnk.args = [self.magicc_excdata]
                            else:   # When the program tries to create a new exception
                                lnk.args = [self.pack_excvar(lnk.args[0], lnk.args[1], blk)]

    def pack_exccnst(self, cnst_type, cnst_value):
        """
        Pack the exception type and value Constants into a MuPyExcData constant
        """
        ptr_excdata = lltype.malloc(self.ptr_excdata_llt.TO, immortal=True)
        ptr_excdata._obj.exc_type = cnst_type
        ptr_excdata._obj.exc_value = cnst_value

        cnst = Constant(ptr_excdata, self.ptr_excdata_llt)
        cnst.concretetype = self.ptr_excdata_llt

        return cnst

    def pack_excvar(self, var_type, var_value, blk):
        """
        Pack the exception type and value variables into a newly created MuPyExcData variable
        by instructions
        """
        excdata = Variable('excdata')
        excdata.concretetype = self.ptr_excdata_llt
        blk.operations.append(
            SpaceOperation('malloc',
                           [Constant(self.ptr_excdata_llt.TO, lltype.Void)],
                           excdata))
        blk.operations.append(
            SpaceOperation('setfield',
                           [excdata, Constant('exc_type', lltype.Void), var_type],
                           None))
        blk.operations.append(
            SpaceOperation('setfield',
                           [excdata, Constant('exc_value', lltype.Void), var_value],
                           None))

        return excdata

    def exctran(self, g):
        """
        Perform exception transform on graph.

        :param g: rpython.flowspace.model.FunctionGraph
        :return: None
        """
        # Transform the raise block
        assert isinstance(g, FunctionGraph)
        var_excdata = Variable('excdata')
        var_excdata.concretetype = self.ptr_excdata_llt
        g.exceptblock.inputargs = [var_excdata]
        g.exceptblock.operations = [SpaceOperation('mu_throw', [g.exceptblock.inputargs[0]], None)]

        # Transform the links
        self.linktran(g)

        # create catch and compare blocks for blocks that have more than 2 exits,
        # and asserts that c_last_exception has to be the exitswitch

        # from rpython.translator.mu.tools.textdisp import _print_graph
        # _print_graph(g)
        blks = [b for b in g.iterblocks()]
        for blk in blks:
            if blk.exitswitch == c_last_exception:
                self.catch_and_compare(blk)

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

    def create_link(self, src_blk, dst_blk, args):
        lnk = Link(args, dst_blk)
        lnk.prevblock = src_blk
        return lnk

    def catch_and_compare(self, blk):
        """
        Create blocks to catch the exception and
        compare it with the desired type

        :param blk: The block that has more than 2 exits.
        :param g: The graph that the block belongs to.
        :return: None
        """
        lnks = blk.exits
        blk_catch = Block([])
        blk.exits = (lnks[0], self.create_link(blk, blk_catch, []))  # Replace the output link
        blk.operations[-1].mu_exc = EXCEPT(DEST(blk.exits[0].target, blk.exits[0].args),
                                           DEST(blk.exits[1].target, blk.exits[1].args))

        excobjptr = Variable("excobjptr")
        excobjptr.concretetype = lltype.Ptr(lltype.OpaqueType('_Void'))
        blk_catch.mu_excparam = excobjptr

        excdataptr = Variable("excdataptr")
        excdataptr.concretetype = self.ptr_excdata_llt
        blk_catch.operations.append(SpaceOperation('cast_pointer', [excobjptr], excdataptr))

        chain = self.create_compare_blocks(lnks[1:])
        blk_catch.exits = (self.create_link(blk_catch, chain,
                                            [excdataptr, lnks[1].llexitcase]), )

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
            return None

        lnk = lnks[0]
        chain = self.create_compare_blocks(lnks[1:])

        # Need to create new variable for parameters
        excdataptr = Variable('excdataptr')
        excdataptr.concretetype = self.ptr_excdata_llt
        typeobj = Variable('typeobj')
        typeobj.concretetype = self.exctype_llt

        blk = Block([excdataptr, typeobj])
        lnk.prevblock = blk

        cmpres = Variable("cmpres")
        cmpres.concretetype = lltype.Bool
        blk.operations.append(
            SpaceOperation('direct_call',
                           [self.mupyexc_checktype, excdataptr, typeobj],
                           cmpres))
        blk.exitswitch = cmpres

        # Handle the case there it attempts to pass the last caught exception value
        if len(lnk.args) == 1 and lnk.args[0] == self.magicc_excvalue:
            excval = Variable('excval')
            excval.concretetype = self.excval_llt
            blk.operations.append(
                SpaceOperation('direct_call',
                               [self.mupyexc_getvalue, excdataptr],
                               excval))
            lnk.args[0] = excval

        if chain:
            blk.exits = (self.create_link(blk, chain, [excdataptr, lnks[1].llexitcase]), lnk)
        else:
            l = lnks[1]
            l.prevblock = blk
            if len(l.args) == 1 and l.args[0] == self.magicc_excdata:
                l.args = [excdataptr]
            blk.exits = (l, lnk)

        return blk

    def get_helpergraphs(self):
        """
        :return: All the created graphs for exception transform.
        """
        def _get_graph(fc):
            return fc.value._obj.graph

        graphs = [_get_graph(self.mupyexc_checktype), _get_graph(self.mupyexc_getvalue)]

        for blk in _get_graph(self.mupyexc_checktype).iterblocks():
            for op in blk.operations:
                if op.opname == 'direct_call':
                    g = _get_graph(op.args[0])
                    if g not in graphs:
                        graphs.append(g)

        for blk in _get_graph(self.mupyexc_getvalue).iterblocks():
            for op in blk.operations:
                if op.opname == 'direct_call':
                    g = _get_graph(op.args[0])
                    if g not in graphs:
                        graphs.append(g)
        return graphs
