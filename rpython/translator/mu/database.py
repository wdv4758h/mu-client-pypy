"""
Mu IR text-form generation code
"""
from rpython.flowspace.model import Constant
from rpython.mutyper.muts.muentity import MuName
from rpython.mutyper.muts import mutype
from rpython.translator.mu.hail import HAILGenerator
from rpython.tool.ansi_mandelbrot import Driver
from rpython.tool.ansi_print import AnsiLogger
import ctypes, ctypes.util
import os, sys
mdb = Driver()


class MuDatabase:
    BUNDLE_ENTRY_NAME = '_mu_bundle_entry'
    bundle_suffix = '.mu'

    def __init__(self, graphs, mutyper, entry_graph):
        self.mutyper = mutyper
        self.prog_entry = entry_graph
        self.gbltypes = {}      # type -> set(Mutype)
        self.gblcnsts = set()
        self.externfncs = set()
        self.dylibs = None
        self.objtracer = HeapObjectTracer()
        self.graphs = graphs
        self.log = AnsiLogger(self.__class__.__name__)

    def collect_gbldefs(self):
        self.log.collect_gbldefs("start collecting...")

        def _trav_symbol(v):
            if hasattr(v, 'mu_type'):
                self._recursive_addtype(v.mu_type)
            if isinstance(v, Constant):
                assert isinstance(v.value, mutype._muobject)
                assert not isinstance(v.value, mutype._muref)
                if isinstance(v.value, mutype._muexternfunc):
                    if not hasattr(v, 'mu_name'):
                        v.mu_name = v.value.mu_name
                        assert v.mu_name
                    self.externfncs.add(v)
                elif isinstance(v.value, mutype._mufuncref):
                    if not hasattr(v, 'mu_name'):
                        assert getattr(v.value, 'graph', False)
                        v.mu_name = v.value.graph.mu_name
                        assert v.mu_name
                else:
                    v.__init__(v.value)     # rehash
                    self.gblcnsts.add(v)
            elif isinstance(v, mutype.MuType):
                self._recursive_addtype(v)

        self.log.collect_gbldefs("traversing graphs...")
        for g in self.graphs:
            _trav_symbol(g)
            for blk in g.iterblocks():
                for arg in blk.mu_inputargs:
                    _trav_symbol(arg)
                for op in blk.mu_operations:
                    map(_trav_symbol, op._args)
                    if 'CALL' in op.opname:
                        map(_trav_symbol, op.args)
                        if isinstance(op.callee, mutype._muexternfunc):
                            self.externfncs.add(op.callee)
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
                            map(_trav_symbol, dst.args)
            mdb.dot()

        self._recursive_addtype(self.mutyper.tlstt_t)

        mdb.restart()

        self.log.objtracer("start tracing heap objects...")
        for gcl in self.mutyper.ldgcells:
            self.objtracer.trace(gcl)

        for t in self.objtracer.get_types():
            self._recursive_addtype(t)

        self.log.objtracer("finished.")

        # for each container type, declare all reference types to that type
        for cont_cls in (mutype.MuStruct, mutype.MuHybrid, mutype.MuArray):
            if cont_cls in self.gbltypes:
                for cont_t in self.gbltypes[cont_cls]:
                    for ref_cls in (mutype.MuRef, mutype.MuIRef, mutype.MuUPtr):
                        if ref_cls not in self.gbltypes:
                            self.gbltypes[ref_cls] = set()
                        ref_t = ref_cls(cont_t)
                        ref_set = self.gbltypes[ref_cls]
                        if ref_t not in ref_set:
                            ref_set.add(ref_t)

        for t in self.objtracer.nullref_ts:
            muv = mutype._munullref(t)
            cst = Constant(muv)
            cst.mu_type = muv._TYPE
            cst.mu_name = MuName("%s_%s" % (str(cst.value), cst.mu_type.mu_name._name))
            self.gblcnsts.add(cst)

        self._process_externfuncs()
        self.log.collect_gbldefs("finished.")

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

    def _process_externfuncs(self):
        def _get_required_libs(extfns):
            if sys.platform.startswith('darwin'):
                for fn in extfns:
                    if 'rt' in fn.eci.libraries:
                        l = list(fn.eci.libraries)
                        l.remove('rt')
                        l.append('System')
                        fn.eci.libraries = tuple(l)
                        
            libraries = [fn.eci.libraries for fn in extfns]
            libs = set()
            for tup_libs in libraries:
                assert len(tup_libs) <= 1   # each c function should only be found in one dylib
                libs.update(tup_libs)
            return libs

        required_libs = _get_required_libs(self.externfncs)
        required_libs.add('c')
        libdic = {}
        # load up the dynamic libraries and find the corresponding functions
        for libabbrv in required_libs:
            ctypes.util.find_library(libabbrv)
            libpath = ctypes.util.find_library(libabbrv)
            if not libpath:
                raise LookupError("library \'%(libabbrv)s not found\'" % locals())
            lib = ctypes.CDLL(libpath)
            libdic[libabbrv] = lib
        # load librpyc.so
        dir_mu = os.path.dirname(__file__)
        dir_librpyc = os.path.join(dir_mu, 'rpyc')
        path_librpyc = os.path.join(dir_librpyc, 'librpyc.so')

        try:
            librpyc = ctypes.CDLL(path_librpyc)
        except OSError as e:
            os.write(2, "ERROR: library {} not found.\n"
                        "Please execute 'make' in the directory {}\n".format(path_librpyc, dir_librpyc))
            raise e
        libdic['rpyc'] = librpyc

        self.dylibs = libdic.values()

        # manage function name mappings
        _pypy_linux_prefix = "__pypy_mu_linux_"
        _pypy_apple_prefix = "__pypy_mu_apple_"
        _pypy_macro_prefix = "__pypy_macro_"
        _LINUX = sys.platform.startswith('linux')
        _APPLE = sys.platform.startswith('darwin')
        def _get_c_symname(extfn):
            """
            Correct some function naming
            especially needed for stat system calls.
            """
            def sym_in_lib(c_symname, lib):
                try:
                    getattr(lib, c_symname)
                    return True
                except AttributeError:
                    return False

            c_name = extfn.c_name
            if _APPLE:
                if c_name in ('stat', 'fstat', 'lstat'):
                    c_name = c_name + '64'  # stat64, fstat64, lstat64
                if c_name == "readdir":  # fixing the macro defined return type (struct dirent*)
                    c_name = _pypy_apple_prefix + c_name

            # find symbol in shared lib
            default_libs = ('rpyc', 'c')
            libdeps = map(libdic.get, extfn.eci.libraries + default_libs)
            for lib in libdeps:
                if sym_in_lib(c_name, lib):
                    return c_name

                for prefix in (_pypy_linux_prefix, _pypy_macro_prefix):
                    if sym_in_lib(prefix + c_name, lib):
                        return prefix + c_name

            # search librpyc.so for last resort.
            for prefix in (_pypy_linux_prefix, _pypy_macro_prefix):
                if sym_in_lib(prefix + c_name, librpyc):
                    return prefix + c_name

            # otherwise fail
            raise LookupError("Failed to find function '%(c_name)s'.\n" % locals())

        for extfn in self.externfncs:
            c_symname = _get_c_symname(extfn)
            extfn.c_symname = c_symname


class HeapObjectTracer:
    def __init__(self):
        self.gcells = {}        # forms a list of roots
        self.objs = set()
        self.nullref_ts = set()

    def trace(self, gcell):
        self._find_refs(gcell._obj)

        # get the top container
        obj = gcell._obj._obj0
        if isinstance(obj, mutype._mustruct):
            obj = obj._top_container()
        self.gcells[gcell] = obj

    def _find_refs(self, obj):
        if isinstance(obj, (mutype._muref, mutype._muiref)):
            refnt = obj._obj0
            if isinstance(refnt, mutype._mustruct):
                refnt = refnt._top_container()

            if refnt not in self.objs:
                self.objs.add(refnt)
                self._find_refs(refnt)

        elif isinstance(obj, (mutype._mustruct, mutype._muhybrid)):
            for fld in mutype.mu_typeOf(obj)._flds:
                self._find_refs(obj._getattr(fld))

        elif isinstance(obj, (mutype._mumemarray)):
            if isinstance(obj._OF, (mutype.MuContainerType, mutype.MuRef, mutype.MuIRef)):
                for i in range(len(obj.items)):
                    itm = obj[i]
                    self._find_refs(itm)
        elif isinstance(obj, mutype._munullref):
            self.nullref_ts.add(obj._TYPE)

    def get_types(self):
        s = set()
        for r in self.objs:
            obj_t = mutype.mu_typeOf(r)
            s.add(obj_t)
        return s.union(self.nullref_ts)