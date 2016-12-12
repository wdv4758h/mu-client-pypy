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
            - create a C function source file that redirects macro calls to function calls
            - find corresponding functions in libraries suggested
            - rename some functions based on platforms
        - trace heap objects
        """
        self.collect_global_defs()

    def collect_global_defs(self):
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

    def _collect_constant(self, c):
        if isinstance(c.concretetype, mutype.MuNumber):
            self.consts.add(c)
        elif isinstance(c.concretetype, mutype.MuGlobalCell):
            self.gcells.add(c)
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
        eci = eci.compile_shared_lib('libpypy_mu_support',
                                     debug_mode=False,      # no '-g -O0'
                                     defines=['RPY_EXTERN=RPY_EXPORTED'])

        # step 4: update eci to include the compiled shared library
        for fnp in replace_ecis:
            fnp.eci = eci

        self.libsupport_path = py.path.local(eci.libraries[-1])
        return eci
