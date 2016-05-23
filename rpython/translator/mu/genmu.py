"""
Mu IR text-form generation code
"""
from rpython.flowspace.model import FunctionGraph, Block, Variable, Constant
from rpython.mutyper.ll2mu import ll2mu_ty, _MuOpList
from rpython.mutyper.muts.muentity import MuName
from rpython.mutyper.muts.muops import CALL, THREAD_EXIT, STORE, GETIREF
from rpython.mutyper.muts import mutype
from .hail import HAILGenerator
from StringIO import StringIO
import zipfile
import json


try:
    import zlib
    zip_compression = zipfile.ZIP_DEFLATED
except ImportError:
    zip_compression = zipfile.ZIP_STORED


class MuTextIRGenerator:
    BUNDLE_ENTRY_NAME = '_mu_bundle_entry'
    bundle_suffix = '.mu'

    def __init__(self, graphs, mutyper, entry_graph):
        self.mutyper = mutyper
        self.prog_entry = entry_graph
        self.gbltypes = set()
        self.gblcnsts = set()

        graphs.append(self._create_bundle_entry(self.prog_entry))
        self.graphs = graphs

    def _create_bundle_entry(self, pe):
        blk = Block([])

        be = FunctionGraph(MuTextIRGenerator.BUNDLE_ENTRY_NAME, blk)
        be.mu_name = MuName(be.name)
        ver = Variable('_ver')
        ver.mu_name = MuName(ver.name, be)
        be.mu_version = ver
        blk.mu_name = MuName("entry", be)

        rtnbox = Variable('rtnbox')
        rtnbox.mu_name = MuName(rtnbox.name, be.startblock)
        rtnbox.mu_type = mutype.MuRef(pe.mu_type.Sig.RTNS[0])
        blk.inputargs = pe.startblock.inputargs + [rtnbox]

        be.mu_type = mutype.MuFuncRef(mutype.MuFuncSig(map(lambda arg: arg.mu_type, blk.inputargs), ()))
        _recursive_addtype(self.gbltypes, be.mu_type)
        ops = _MuOpList()
        rtn = ops.append(CALL(pe, tuple(pe.startblock.inputargs)))
        rtn.mu_name.scope = blk
        irfrtnbox = ops.append(GETIREF(rtnbox))
        ops.append(STORE(irfrtnbox, rtn))
        ops.append(THREAD_EXIT())
        blk.operations = tuple(ops)
        return be

    def bundlegen(self, bdlpath):
        strio_ir = StringIO()
        strio_hail = StringIO()
        strio_exfn = StringIO()
        self.codegen(strio_ir, strio_hail, strio_exfn)

        zf = zipfile.ZipFile(bdlpath.strpath, mode="w", compression=zip_compression)

        def _writefrom(entry_name, strio):
            s = strio.getvalue()
            strio.close()
            print s
            zf.writestr(entry_name, s)

        _writefrom(bdlpath.basename.replace('.mu', '.uir'), strio_ir)
        _writefrom(bdlpath.basename.replace('.mu', '.hail'), strio_hail)
        _writefrom(bdlpath.basename.replace('.mu', '.exfn'), strio_exfn)

        zf.close()

    def codegen(self, fp_ir, fp_hail, fp_exfn):
        """
        Generate bundle code to a writable file fp.
        """
        self._collect_gbldefs()
        for t in self.gbltypes:
            fp_ir.write("%s %s = %s\n" % (".funcsig" if isinstance(t, mutype.MuFuncSig) else ".typedef",
                                          t.mu_name, t.mu_constructor))

        for cst in self.gblcnsts:
            fp_ir.write(".const %s <%s> = %r\n" % (cst.mu_name, cst.mu_type.mu_name, cst.value))

        hailgen = HAILGenerator()
        for gcell in self.mutyper.ldgcells:
            fp_ir.write(".global %s <%s>\n" % (gcell.mu_name, gcell._T.mu_name))
            hailgen.add_gcell(gcell)
        hailgen.codegen(fp_hail)

        fncs = []
        for gcl in self.mutyper.externfncs:
            fp_ir.write(".global %s <%s>\n" % (gcl.mu_name, gcl._T.mu_name))
            fncs.append((gcl.c_name, str(gcl._T.mu_name), str(gcl.mu_name), gcl.c_libs))
        fp_exfn.write(json.dumps(fncs))

        for g in self.graphs:
            fp_ir.write(".funcdef %s VERSION %s <%s> {\n" % (g.mu_name, g.mu_version.mu_name,
                                                             g.mu_type.Sig.mu_name))
            self._genblocks(g, fp_ir)
            fp_ir.write("}\n")

    def _genblocks(self, g, fp):
        idt = 4     # indentation
        for blk in g.iterblocks():
            fp.write('%s%s(%s)%s:\n' % (
                ' ' * idt, blk.mu_name,
                ' '.join(["<%s> %s" % (arg.mu_type.mu_name, arg.mu_name) for arg in blk.inputargs]),
                '[%s]' % blk.mu_excparam.mu_name if hasattr(blk, 'mu_excparam') else ''
            ))
            for op in blk.operations:
                fp.write("%s%s\n" % (' ' * idt * 2, op))

    def _collect_gbldefs(self):
        def _trav_symbol(v):
            if hasattr(v, 'mu_type'):
                _recursive_addtype(self.gbltypes, v.mu_type)
            if isinstance(v, Constant):
                assert isinstance(v.value, mutype._muobject)
                if isinstance(v.value, mutype._mufuncref):
                    if not hasattr(v, 'mu_name'):
                        assert getattr(v.value, 'graph', False)
                        v.mu_name = v.value.graph.mu_name
                else:
                    v.__init__(v.value)     # rehash
                    self.gblcnsts.add(v)

        for g in self.graphs:
            _trav_symbol(g)
            for blk in g.iterblocks():
                for arg in blk.inputargs:
                    _trav_symbol(arg)
                for op in blk.operations:
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

        def _add_parent_types(stt):
            stt_norm = stt._top_container()
            _recursive_addtype(self.gbltypes, stt_norm._TYPE)
            # while stt._parent:
            #     prnt = stt._parent
            #     _recursive_addtype(self.gbltypes, prnt._TYPE)
            #     stt = prnt

        def _trav_refval(ref):
            def _trav_sttval(obj):
                _recursive_addtype(self.gbltypes, obj._TYPE)
                for fld in obj._TYPE._names:
                    fldval = getattr(obj, fld)
                    if isinstance(fldval, mutype._muref):
                        _trav_refval(fldval)
                    elif isinstance(fldval, mutype._mustruct):
                        _trav_sttval(fldval)

            if not isinstance(ref, mutype._munullref):
                _recursive_addtype(self.gbltypes, ref._TYPE)
                obj = ref._obj0
                if isinstance(obj, mutype._mustruct):
                    _trav_sttval(obj._top_container())
                elif isinstance(obj, mutype._muhybrid):
                    arr = getattr(obj, obj._TYPE._varfld)
                    if isinstance(arr._OF, mutype.MuRef):
                        for itm in arr:
                            _trav_refval(itm)

        for gcl in self.mutyper.ldgcells:
            _trav_refval(gcl.value)


def _recursive_addtype(s_types, mut):
    if mut not in s_types:
        s_types.add(mut)
        if isinstance(mut, (mutype.MuStruct, mutype.MuHybrid)):
            fld_ts = tuple(getattr(mut, fld) for fld in mut._names)
            for t in fld_ts:
                _recursive_addtype(s_types, t)
        elif isinstance(mut, mutype.MuArray):
            _recursive_addtype(s_types, mut.OF)
        elif isinstance(mut, mutype.MuRef):
            _recursive_addtype(s_types, mut.TO)
        elif isinstance(mut, mutype.MuFuncRef):
            _recursive_addtype(s_types, mut.Sig)
        elif isinstance(mut, mutype.MuFuncSig):
            ts = mut.ARGS + mut.RTNS
            for t in ts:
                _recursive_addtype(s_types, t)
