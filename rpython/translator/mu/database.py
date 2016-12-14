from rpython.flowspace.model import Constant
from rpython.rtyper.lltypesystem import lltype, rffi
from rpython.translator.mu import mutype
from rpython.translator.platform import platform
from rpython.tool.udir import udir
import ctypes, ctypes.util
import os, sys, py

from rpython.tool.ansi_mandelbrot import Driver
from rpython.tool.ansi_print import AnsiLogger
mdb = Driver()


class MuDatabase:
    def __init__(self, tlc):
        # type: (rpython.translator.translator.TranslationContext) -> None
        self.tlc = tlc
        self.types = set()
        self.consts = set()
        self.funcref_consts = set()
        self.gcells = set()
        self.extern_fncs = set()
        self.objtracer = None
        self.libsupport_path = None
        self.mu_name_map = {}

    def build_database(self):
        """
        Tasks to be done at database stage:
        - lower the debug operations to mu_ccalls
        - collect all global definitions
            - types
            - constants
            - external functions
            - global cells
            - graphs & function references
        - assign a Mu name to each global entity and local variable
        - process external C functions
            - compiling C function macros,
                        C function declared in post_include_bits,
                        and C functions defined in PyPy C backend into one shared library
            - update the ecis, and rename function names
        - trace heap objects
        """
        self.collect_global_defs()
        self.compile_pypy_c_extern_funcs()
        self.assign_mu_name()

    def collect_global_defs(self):
        # collect global definitions in graphs
        for graph in self.tlc.graphs:
            try:
                ret_t = graph.getreturnvar().concretetype
            except IndexError:
                ret_t = mutype.MU_VOID

            self._add_type(mutype.MuFuncSig(map(lambda v: v.concretetype, graph.getargs()), [ret_t]))

            for blk in graph.iterblocks():
                for a in blk.inputargs:
                    self._add_type(a.concretetype)
                for op in blk.operations:
                    for a in op.args:
                        self._add_type(a.concretetype)
                        if isinstance(a, Constant):
                            self._collect_constant(a)
                    self._add_type(op.result.concretetype)
                for lnk in blk.exits:
                    for a in lnk.args:
                        self._add_type(a.concretetype)
                        if isinstance(a, Constant):
                            self._collect_constant(a)
                    if isinstance(lnk.exitcase, Constant):
                        self._collect_constant(lnk.exitcase)

        # trace heap objects
        self.objtracer = HeapObjectTracer()

        for gcl in self.gcells:
            self.objtracer.trace(gcl.value._load())

        # add types in heap to global type definitions
        for t in self.objtracer.types_in_heap():
            self._add_type(t)

    def _collect_constant(self, c):
        if isinstance(c.concretetype, mutype.MuNumber):
            self.consts.add(c)
        elif isinstance(c.concretetype, mutype.MuGlobalCell):
            self.gcells.add(c)
        elif isinstance(c.concretetype, mutype.MuReferenceType) and c.value._is_null():
            self.consts.add(c)
        elif isinstance(c.concretetype, mutype.MuUFuncPtr):
            self.extern_fncs.add(c)
        elif isinstance(c.concretetype, mutype.MuFuncRef):
            self.funcref_consts.add(c)

    def _add_type(self, T):
        assert isinstance(T, mutype.MuType)

        if isinstance(T, mutype.MuGlobalCell):
            T = T.TO

        if T in self.types:
            return

        self.types.add(T)

        if isinstance(T, mutype.MuStruct):
            for FLD in tuple(getattr(T, fld) for fld in T._names):
                self._add_type(FLD)
        elif isinstance(T, mutype.MuHybrid):
            for FLD in tuple(getattr(T, fld) for fld in T._names[:-1]):
                self._add_type(FLD)
            self._add_type(T._vartype.OF)
        elif isinstance(T, mutype.MuArray):
            self._add_type(T.OF)
        elif isinstance(T, mutype.MuObjectRef):
            self._add_type(T.TO)
        elif isinstance(T, mutype.MuGeneralFunctionReference):
            self._add_type(T.Sig)
        elif isinstance(T, mutype.MuFuncSig):
            ts = T.ARGS + T.RESULTS
            for t in ts:
                self._add_type(t)

    def compile_pypy_c_extern_funcs(self):
        all_ecis = []
        replace_ecis = []
        header_file_name = 'mu_common_header.h'
        header_file_dir_path = udir.strpath

        # step 1: identify macros, functions defined in post_include_bits
        for c in self.extern_fncs:
            fnp = c.value
            eci = fnp.eci

            if eci.post_include_bits:
                if any(fnp._name in s for s in eci.post_include_bits):      # C function declaration
                    # wrap in a macro (renaming will be done below)
                    # rely on clang -O3 optimisation to inline
                    _macro_fnp = rffi.llexternal(fnp._name, fnp._llfnctype.ARGS, fnp._llfnctype.RESULT,
                                                 compilation_info=eci,
                                                 macro=True, _nowrapper=True)
                    eci = _macro_fnp._obj.compilation_info

            if hasattr(eci, '_with_ctypes'):
                # function in the same module with macros (same eci)
                eci = eci._with_ctypes
                fnp.eci = eci   # reassign the eci
                for src_str in eci.separate_module_sources:
                    if fnp._name in src_str:    # is a macro
                        fnp._name = 'pypy_macro_wrapper_' + fnp._name
                        break

            if eci.post_include_bits or eci.separate_module_sources or eci.separate_module_files:
                replace_ecis.append(fnp)

            all_ecis.append(eci)

        pypy_include_dir = py.path.local(__file__).join('..', '..', 'c')
        eci = rffi.ExternalCompilationInfo(include_dirs=[pypy_include_dir.strpath])
        eci = eci.merge(*all_ecis).convert_sources_to_files()

        # step 2: convert all separate module sources to files
        header_file = udir.join(header_file_name)
        with header_file.open('w') as fp:
            fp.write('#ifndef _PY_COMMON_HEADER_H\n#define _PY_COMMON_HEADER_H\n')
            eci.write_c_header(fp)
            fp.write('#include "src/g_prerequisite.h"\n')
            fp.write('#endif /* _PY_COMMON_HEADER_H*/\n')

        # add common header to eci
        eci.post_include_bits = ()  # should have been written to mu_common_header.h
        eci = eci.merge(rffi.ExternalCompilationInfo(includes=[header_file_name], include_dirs=[header_file_dir_path]))

        # step 3: compile these files into shared library
        eci = eci.compile_shared_lib(platform.so_prefixes[0] + 'pypy_mu_support',
                                     debug_mode=False,      # no '-g -O0'
                                     defines=['RPY_EXTERN=RPY_EXPORTED'])

        # step 4: update eci to include the compiled shared library
        for fnp in replace_ecis:
            fnp.eci = eci

        self.libsupport_path = py.path.local(eci.libraries[-1])
        return eci

    def assign_mu_name(self):
        man = MuNameManager()
        # types
        for T in self.types:
            self.mu_name_map[T] = man.assign(T)

        # constants
        for c in self.consts:
            self.mu_name_map[c] = man.assign(c)

        for c in self.extern_fncs:
            self.mu_name_map[c] = '@extfnc_' + c.value._name

        # global cells
        for c in self.gcells:
            self.mu_name_map[c] = man.assign(c)

        # graphs
        for g in self.tlc.graphs:
            graph_name = '@' + g.name
            self.mu_name_map[g] = graph_name
            for i, blk in enumerate(g.iterblocks()):
                blk_name = '%(graph_name)s.blk%(i)d' % locals()
                self.mu_name_map[blk] = blk_name

                for v in blk.inputargs:
                    self.mu_name_map[v] = '%(blk_name)s.%(v)s' % locals()
                for op in blk.operations:
                    res = op.result
                    self.mu_name_map[res] = '%(blk_name)s.%(res)s' % locals()


class HeapObjectTracer:
    def __init__(self):
        self.objs = set()
        self.uptrs = set()  # objects pointed to by uptr, needs relocation support
        self.nullref_ts = set()
        self.types = set()

    def trace(self, obj):
        MuT = mutype.mutypeOf(obj)
        if not isinstance(MuT, mutype._MuMemArray):
            self.types.add(MuT)

        if isinstance(obj, mutype._muobject_reference):
            if obj._is_null():
                self.nullref_ts.add(mutype.mutypeOf(obj))
                return

            refnt = obj._obj
            if isinstance(refnt, mutype._mustruct):
                refnt = refnt._normalizedcontainer()

            if refnt not in self.objs:
                self.objs.add(refnt)
                self.trace(refnt)

            if isinstance(obj, mutype._muuptr):
                self.uptrs.add(refnt)

        elif isinstance(obj, (mutype._mustruct, mutype._muhybrid)):
            for fld in mutype.mutypeOf(obj)._flds:
                self.trace(getattr(obj, fld))

        elif isinstance(obj, (mutype._mumemarray, mutype._muarray)):
            if isinstance(mutype.mutypeOf(obj).OF, (mutype.MuContainerType, mutype.MuObjectRef)):
                for i in range(len(obj.items)):
                    itm = obj[i]
                    self.trace(itm)

    def types_in_heap(self):
        return self.types


class MuNameManager:
    def __init__(self):
        self.name_map = {
            mutype.MU_FLOAT: '@flt',
            mutype.MU_DOUBLE: '@dbl',
            mutype.MU_VOID: '@void',
        }
        self._counter = {
            'stt': 0,
            'hyb': 0,
            'arr': 0,
            'gcl': 0,
        }

    def assign(self, obj):
        if isinstance(obj, mutype.MuType):
            return self.get_type_name(obj)
        if isinstance(obj, Constant):
            return self.get_const_name(obj)

    def get_type_name(self, MuT):
        if MuT in self.name_map:
            return self.name_map[MuT]

        if isinstance(MuT, mutype.MuIntType):
            name = 'i%d' % MuT.BITS

        if isinstance(MuT, mutype.MuStruct):
            name = 'stt%d' % self._counter['stt']
            self._counter['stt'] += 1

        if isinstance(MuT, mutype.MuHybrid):
            name = 'hyb%d' % self._counter['hyb']
            self._counter['hyb'] += 1

        if isinstance(MuT, mutype.MuArray):
            name = 'arr%d' % self._counter['arr']
            self._counter['arr'] += 1

        if isinstance(MuT, mutype.MuReferenceType):
            prefix_map = {
                mutype.MuRef: 'ref',
                mutype.MuIRef: 'irf',
                mutype.MuUPtr: 'ptr',
                mutype.MuWeakRef: 'wrf',
                mutype.MuFuncRef: 'fnr',
                mutype.MuUFuncPtr: 'fnp',
                mutype.MuOpaqueRef: 'opqr'
            }
            prefix = prefix_map[type(MuT)]
            if isinstance(MuT, mutype.MuObjectRef):
                refnt = self.get_type_name(MuT.TO)[1:]
                name = prefix + refnt
            elif isinstance(MuT, mutype.MuGeneralFunctionReference):
                sig = self.get_type_name(MuT.Sig)[1:]
                name = prefix + sig
            elif isinstance(MuT, mutype.MuOpaqueRef):
                name = prefix + MuT.obj_name

        if isinstance(MuT, mutype.MuFuncSig):
            name = 'sig_%(args)s_%(rets)s' % {
                'args': ''.join([self.get_type_name(T)[1:] for T in MuT.ARGS]),
                'rets': ''.join([self.get_type_name(T)[1:] for T in MuT.RESULTS])
            }

        name = '@' + name
        self.name_map[MuT] = name
        return name

    def get_const_name(self, const):
        if isinstance(const.concretetype, mutype.MuGlobalCell):
            name = 'gcl%d' % self._counter['gcl']
            self._counter['gcl'] += 1
        elif isinstance(const.concretetype, mutype.MuReferenceType) and const.value._is_null():
            name = 'NULL_%s' % self.get_type_name(const.concretetype)
        elif isinstance(const.concretetype, mutype.MuNumber):
            name = '%(hex)s_%(type)s' % {'hex': mutype.hex_repr(const.value),
                                         'type': self.get_type_name(const.concretetype)[1:]}
        return '@' + name
