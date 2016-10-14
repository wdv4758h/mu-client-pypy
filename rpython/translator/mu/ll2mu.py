from rpython.rtyper.lltypesystem import lltype, llmemory, rffi
from rpython.translator.mu import mutype
from rpython.rtyper.normalizecalls import TotalOrderSymbolic
from rpython.rlib.objectmodel import CDefinedIntSymbolic
from rpython.rlib import rarithmetic
from rpython.flowspace.model import Constant, SpaceOperation
from rpython.translator.c.node import needs_gcheader
from random import randint

from rpython.tool.ansi_print import AnsiLogger
from rpython.tool.ansi_mandelbrot import Driver

log = AnsiLogger("ll2mu")
mdb = Driver()


class LL2MuMapper:
    GC_IDHASH_FIELD = ('gc_idhash', mutype.MU_INT64)

    def __init__(self):
        self._type_cache = {}
        self._referents_to_resolve = []
        self._name_cache = {}

    def _new_typename(self, name):
        if name not in self._name_cache:
            n = 2
            self._name_cache[name] = n
            return name
        n = self._name_cache[name]
        self._name_cache[name] = n + 1
        return "%(name)s_%(n)d" % locals()

    def map_type(self, LLT):
        assert isinstance(LLT, lltype.LowLevelType)
        try:
            return self._type_cache[LLT]
        except KeyError:
            if LLT is llmemory.Address:
                MuT = self.map_type_addr(LLT)
            elif isinstance(LLT, lltype.Primitive):
                MuT = self.map_type_prim(LLT)
            elif isinstance(LLT, lltype.FixedSizeArray):
                MuT = self.map_type_arrfix(LLT)
            elif isinstance(LLT, lltype.Struct):
                MuT = self.map_type_stt(LLT)
            elif isinstance(LLT, lltype.Array):
                MuT = self.map_type_arr(LLT)
            elif isinstance(LLT, lltype.Ptr):
                MuT = self.map_type_ptr(LLT)
            elif isinstance(LLT, lltype.FuncType):
                MuT = self.map_type_func(LLT)
            elif isinstance(LLT, lltype.OpaqueType):
                MuT = self.map_type_opq(LLT)
            elif LLT is llmemory.WeakRef:
                MuT = self.map_type_wref(LLT)
            else:
                raise NotImplementedError("Don't know how to specialise %s using MuTS." % LLT)
            self._type_cache[LLT] = MuT
            return MuT

    def map_type_prim(self, LLT):
        type_map = {
            lltype.Signed:              mutype.MU_INT64,
            lltype.Unsigned:            mutype.MU_INT64,
            lltype.SignedLongLong:      mutype.MU_INT64,
            lltype.UnsignedLongLong:    mutype.MU_INT64,
            lltype.SignedLongLongLong:  mutype.MU_INT128,

            lltype.Float:               mutype.MU_DOUBLE,
            lltype.SingleFloat:         mutype.MU_FLOAT,
            lltype.LongFloat:           mutype.MU_DOUBLE,

            lltype.Char:                mutype.MU_INT8,
            lltype.Bool:                mutype.MU_INT8,
            lltype.Void:                mutype.MU_VOID,
            lltype.UniChar:             mutype.MU_INT16,
        }
        try:
            return type_map[LLT]
        except KeyError:
            if isinstance(LLT, lltype.Number) and \
                            LLT._type in rarithmetic._inttypes.values():
                b = LLT._type.BITS
                return mutype.MuIntType("MU_INT%d" % b,
                                        rarithmetic.build_int('r_uint%d', False, b))    # unsigned
            raise NotImplementedError("Don't know how to specialise %s using MuTS." % LLT)

    def map_type_arrfix(self, LLT):
        return mutype.MuArray(self.map_type(LLT.OF), LLT.length)

    def map_type_stt(self, LLT):
        if LLT._is_varsize():
            return self.map_type_varstt(LLT)

        if __name__ == '__main__':
            if len(LLT._names) == 0:    # empty struct
                # Mu does not support empty struct
                # From the spec:
                #   In Mu, if it is desired to allocate an empty unit in the heap,
                #   the appropriate type is `void`
                return mutype.MU_VOID

        flds = []
        if needs_gcheader(LLT):
            flds.append(LL2MuMapper.GC_IDHASH_FIELD)

        for n in LLT._names:
            MuT = self.map_type(LLT._flds[n])
            if MuT is not mutype.MU_VOID:
                flds.append((n, MuT))

        name = self._new_typename(LLT._name)
        return mutype.MuStruct(name, *flds)

    def map_type_varstt(self, LLT):
        VarT = self.map_type(LLT._flds[LLT._arrayfld].OF)

        _names = LLT._names_without_voids()[:-1]
        _flds = LLT._flds.copy()
        if 'length' not in _names:
            _names.append('length')
            _flds['length'] = lltype.Signed

        flds = [(n, self.map_type(_flds[n])) for n in _names] + \
               [(LLT._arrayfld, VarT)]
        if needs_gcheader(LLT):
            flds.insert(0, LL2MuMapper.GC_IDHASH_FIELD)

        name = self._new_typename("%s" % LLT.OF.__name__
                                  if hasattr(LLT.OF, '__name__')
                                  else str(LLT.OF))
        return mutype.MuHybrid(name, *flds)

    def map_type_arr(self, LLT):
        name = "%s" % LLT.OF.__name__ \
            if hasattr(LLT.OF, '__name__') \
            else str(LLT.OF)

        if LLT.OF is lltype.Void:
            return mutype.MuStruct(name, ('length', mutype.MU_INT64))

        flds = ['items', self.map_type(LLT.OF)]
        if not LLT._hints.get('nolength', False):
            flds.insert(0, ('length', mutype.MU_INT64))

        if needs_gcheader(LLT):
            flds.insert(0, LL2MuMapper.GC_IDHASH_FIELD)

        return mutype.MuHybrid(name, *flds)

    def map_type_ptr(self, LLT):
        if LLT.TO._gckind == 'gc':
            cls = mutype.MuRef
        else:
            cls = mutype.MuUPtr

        MuObjT = mutype.MuForwardReference()
        self._referents_to_resolve.append((LLT.TO, MuObjT))
        return cls(MuObjT)

    def resolve_ptrs(self):
        for LLObjT, MuObjT in self._referents_to_resolve:
            MuObjT.become(self.map_type(LLObjT))

    def map_type_addr(self, LLT):
        return mutype.MU_INT64  # all Address types are mapped to int<64>

    def map_type_opq(self, LLT):
        if LLT is lltype.RuntimeTypeInfo:
            return self.map_type(lltype.Char)   # rtti is defined to be a char in C backend.

        MuT = mutype.MU_INT64   # default to int<64>
        return MuT
