"""
Mu IR text-form generation code
"""
from rpython.flowspace.model import FunctionGraph, Block, Variable, Constant
from rpython.mutyper.ll2mu import _MuOpList
from rpython.mutyper.muts.muentity import MuName
from rpython.mutyper.muts.muops import CALL, THREAD_EXIT, STORE, GETIREF
from rpython.mutyper.muts import mutype
from rpython.tool.ansi_mandelbrot import Driver
from rpython.tool.ansi_print import AnsiLogger
log = AnsiLogger("MuTextIRGenerator")
mdb = Driver()


class MuDatabase:
    BUNDLE_ENTRY_NAME = '_mu_bundle_entry'
    bundle_suffix = '.mu'

    def __init__(self, graphs, mutyper, entry_graph):
        self.mutyper = mutyper
        self.prog_entry = entry_graph
        self.gbltypes = {}      # type -> set(Mutype)
        self.gblcnsts = set()

        graphs.append(self._create_bundle_entry(self.prog_entry))
        self.graphs = graphs

    def _create_bundle_entry(self, pe):
        blk = Block([])
        blk.mu_inputargs = []

        be = FunctionGraph(MuDatabase.BUNDLE_ENTRY_NAME, blk)
        be.mu_name = MuName(be.name)
        ver = Variable('_ver')
        ver.mu_name = MuName(ver.name, be)
        be.mu_version = ver
        blk.mu_name = MuName("entry", be)

        rtnbox = Variable('rtnbox')
        rtnbox.mu_name = MuName(rtnbox.name, be.startblock)
        rtnbox.mu_type = mutype.MuRef(pe.mu_type.Sig.RTNS[0])
        blk.mu_inputargs = pe.startblock.mu_inputargs + [rtnbox]

        be.mu_type = mutype.MuFuncRef(mutype.MuFuncSig(map(lambda arg: arg.mu_type, blk.mu_inputargs), ()))
        self._recursive_addtype(be.mu_type)
        ops = _MuOpList()
        rtn = ops.append(CALL(pe, tuple(pe.startblock.mu_inputargs)))
        rtn.mu_name.scope = blk
        irfrtnbox = ops.append(GETIREF(rtnbox))
        ops.append(STORE(irfrtnbox, rtn))
        ops.append(THREAD_EXIT())
        blk.mu_operations = tuple(ops)
        return be

    def collect_gbldefs(self):
        log.collect_gbldefs("start collecting...")

        def _trav_symbol(v):
            if hasattr(v, 'mu_type'):
                self._recursive_addtype(v.mu_type)
            if isinstance(v, Constant):
                assert isinstance(v.value, mutype._muobject)
                if isinstance(v.value, mutype._mufuncref):
                    if not hasattr(v, 'mu_name'):
                        assert getattr(v.value, 'graph', False)
                        v.mu_name = v.value.graph.mu_name
                else:
                    v.__init__(v.value)     # rehash
                    self.gblcnsts.add(v)

        log.collect_gbldefs("traversing graphs...")
        for g in self.graphs:
            _trav_symbol(g)
            for blk in g.iterblocks():
                for arg in blk.mu_inputargs:
                    _trav_symbol(arg)
                for op in blk.mu_operations:
                    map(_trav_symbol, op._args)
                    if 'CALL' in op.opname:
                        map(_trav_symbol, op.args)
                    if op.opname == 'BRANCH':
                        map(_trav_symbol, op.dest.args)
                    if op.opname == 'BRANCH2':
                        map(_trav_symbol, op.ifTrue.args)
                        map(_trav_symbol, op.ifFalse.args)
                        _trav_symbol(op.cond)
                    if op.opname == 'SWITCH':
                        _trav_symbol(op.opnd)
                        map(_trav_symbol, op.default.args)
                        for v, d in op.cases:
                            _trav_symbol(v)
                            map(_trav_symbol, d.args)
                    for attr in "exc nor".split(' '):
                        dst = getattr(op.exc, attr)
                        if dst:
                            _trav_symbol(dst.args)
            mdb.dot()

        _seen_sttval = set()
        def _trav_refval(ref):
            def _trav_sttval(obj):
                if obj in _seen_sttval:
                    return
                _seen_sttval.add(obj)
                self._recursive_addtype(obj._TYPE)
                for fld in obj._TYPE._names:
                    fldval = getattr(obj, fld)
                    if isinstance(fldval, mutype._muref):
                        _trav_refval(fldval)
                    elif isinstance(fldval, mutype._mustruct):
                        _trav_sttval(fldval)

            if not isinstance(ref, mutype._munullref):
                self._recursive_addtype(ref._TYPE)
                obj = ref._obj0
                if isinstance(obj, mutype._mustruct):
                    _trav_sttval(obj._top_container())
                elif isinstance(obj, mutype._muhybrid):
                    arr = getattr(obj, obj._TYPE._varfld)

                    if isinstance(arr._OF, mutype.MuRef):
                        fn = _trav_refval
                    elif isinstance(arr._OF, mutype.MuStruct):
                        fn = _trav_sttval
                    else:
                        fn = None
                    if fn:
                        for itm in arr:
                            fn(itm)

        mdb.restart()
        log.collect_gbldefs("traversing global cells...")
        _seen_sttval = set()
        for gcl in self.mutyper.ldgcells:
            _trav_refval(gcl.value)
            mdb.dot()

        self._recursive_addtype(self.mutyper.tlstt_t)

        mdb.restart()
        log.collect_gbldefs("finished.")

    def _recursive_addtype(self, mut):
        key = mut.__class__
        if key not in self.gbltypes:
            self.gbltypes[key] = set()

        s = self.gbltypes[key]
        if mut not in s:
            s.add(mut)
            if isinstance(mut, (mutype.MuStruct, mutype.MuHybrid)):
                fld_ts = tuple(getattr(mut, fld) for fld in mut._names)
                for t in fld_ts:
                    self._recursive_addtype(t)
            elif isinstance(mut, mutype.MuArray):
                self._recursive_addtype(mut.OF)
            elif isinstance(mut, mutype.MuRef):
                self._recursive_addtype(mut.TO)
            elif isinstance(mut, mutype.MuFuncRef):
                self._recursive_addtype(mut.Sig)
            elif isinstance(mut, mutype.MuFuncSig):
                ts = mut.ARGS + mut.RTNS
                for t in ts:
                    self._recursive_addtype(t)
