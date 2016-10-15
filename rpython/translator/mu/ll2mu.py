from rpython.rtyper.lltypesystem import lltype, llmemory, rffi
from rpython.translator.mu import mutype, layout
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


class LL2MuTypeMapper:
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

    def map(self, LLT):
        assert isinstance(LLT, lltype.LowLevelType)
        try:
            return self._type_cache[LLT]
        except KeyError:
            if LLT is llmemory.Address:
                MuT = self.map_addr(LLT)
            elif isinstance(LLT, lltype.Primitive):
                MuT = self.map_prim(LLT)
            elif isinstance(LLT, lltype.FixedSizeArray):
                MuT = self.map_arrfix(LLT)
            elif isinstance(LLT, lltype.Struct):
                MuT = self.map_type_stt(LLT)
            elif isinstance(LLT, lltype.Array):
                MuT = self.map_arr(LLT)
            elif isinstance(LLT, lltype.Ptr):
                MuT = self.map_ptr(LLT)
            elif isinstance(LLT, lltype.OpaqueType):
                MuT = self.map_opq(LLT)
            elif LLT is llmemory.WeakRef:
                MuT = self.map_wref(LLT)
            else:
                raise NotImplementedError("Don't know how to specialise %s using MuTS." % LLT)
            self._type_cache[LLT] = MuT
            return MuT

    def map_prim(self, LLT):
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

    def map_arrfix(self, LLT):
        return mutype.MuArray(self.map(LLT.OF), LLT.length)

    def map_type_stt(self, LLT):
        if LLT._is_varsize():
            return self.map_varstt(LLT)

        if __name__ == '__main__':
            if len(LLT._names) == 0:    # empty struct
                # Mu does not support empty struct
                # From the spec:
                #   In Mu, if it is desired to allocate an empty unit in the heap,
                #   the appropriate type is `void`
                return mutype.MU_VOID

        flds = []
        if needs_gcheader(LLT):
            flds.append(LL2MuTypeMapper.GC_IDHASH_FIELD)

        for n in LLT._names:
            MuT = self.map(LLT._flds[n])
            if MuT is not mutype.MU_VOID:
                flds.append((n, MuT))

        name = self._new_typename(LLT._name)
        return mutype.MuStruct(name, *flds)

    def map_varstt(self, LLT):
        VarT = self.map(LLT._flds[LLT._arrayfld].OF)

        _names = LLT._names_without_voids()[:-1]
        _flds = LLT._flds.copy()
        if 'length' not in _names:
            _names.append('length')
            _flds['length'] = lltype.Signed

        flds = [(n, self.map(_flds[n])) for n in _names] + \
               [(LLT._arrayfld, VarT)]
        if needs_gcheader(LLT):
            flds.insert(0, LL2MuTypeMapper.GC_IDHASH_FIELD)

        name = self._new_typename(LLT._name)
        return mutype.MuHybrid(name, *flds)

    def map_arr(self, LLT):
        name = "%s" % LLT.OF.__name__ \
            if hasattr(LLT.OF, '__name__') \
            else str(LLT.OF)

        if LLT.OF is lltype.Void:
            return mutype.MuStruct(name, ('length', mutype.MU_INT64))

        flds = ['items', self.map(LLT.OF)]
        if not LLT._hints.get('nolength', False):
            flds.insert(0, ('length', mutype.MU_INT64))

        if needs_gcheader(LLT):
            flds.insert(0, LL2MuTypeMapper.GC_IDHASH_FIELD)

        return mutype.MuHybrid(name, *flds)

    def map_ptr(self, LLT):
        if isinstance(LLT.TO, lltype.FuncType):
            return self.map_funcptr(LLT)

        if LLT.TO._gckind == 'gc':
            cls = mutype.MuRef
        else:
            cls = mutype.MuUPtr

        MuObjT = mutype.MuForwardReference()
        self._referents_to_resolve.append((LLT.TO, MuObjT))
        return cls(MuObjT)

    def resolve_ptrs(self):
        for LLObjT, MuObjT in self._referents_to_resolve:
            MuObjT.become(self.map(LLObjT))

    def map_addr(self, LLT):
        return mutype.MU_INT64  # all Address types are mapped to int<64>

    def map_opq(self, LLT):
        if LLT is lltype.RuntimeTypeInfo:
            return self.map(lltype.Char)   # rtti is defined to be a char in C backend.

        MuT = mutype.MU_INT64   # default to int<64>
        return MuT

    def map_funcptr(self, LLT):
        LLFnc = LLT.TO
        ARG_TS = tuple(self.map(ARG) for ARG in LLFnc.ARGS if ARG != lltype.Void)
        RTN_TS = (self.map(LLFnc.RESULT),)
        sig = mutype.MuFuncSig(ARG_TS, RTN_TS)
        return mutype.MuFuncRef(sig)

    def map_wref(self, LLT):
        return mutype.MuStruct('WeakRef', self.GC_IDHASH_FIELD, ('wref', mutype.MU_WEAKREF_VOID))


# -----------------------------------------------------------------------------
class IgnoredLLVal(NotImplementedError):
    pass

class LL2MuValueMapper:
    def __init__(self, ll2mu_type_mapper):
        self._val_cache = {}
        self._ptr_cache = {}
        self.ll2mu_t = ll2mu_type_mapper
        self._topstt_map = {}
        self._todoptrs = []

    def map(self, llv, **kwargs):
        cache, v = (self._ptr_cache, llv._obj) \
            if isinstance(llv, lltype._ptr) \
            else (self._val_cache, llv)
        LLT = lltype.typeOf(llv)
        key = (LLT, v)
        try:
            return cache[key]
        except KeyError:
            if isinstance(LLT, lltype.Primitive):
                muv = self.map_prim(llv)

            elif isinstance(llv, lltype._fixedsizearray):
                muv = self.map_arrfix(llv)

            elif isinstance(llv, lltype._struct):
                muv = self.map_stt(llv, **kwargs)

            elif isinstance(llv, lltype._array):
                muv = self.map_arr(llv)

            elif isinstance(llv, lltype._ptr):
                muv = self.map_ptr(llv)

            elif isinstance(llv, lltype._opaque):
                muv = self.map_opq(llv)

            elif isinstance(llv, llmemory._wref):
                muv = self.map_wref(llv)

            else:
                raise NotImplementedError(
                    "Don't know how to specialise value %r of type %r." % (llv, lltype.typeOf(llv)))

            if key not in cache:  # may have already been added to cache (in stt to prevent recursion).
                cache[key] = muv
            return muv
        except TypeError, e:
            if isinstance(llv, llmemory.AddressOffset):
                return self.map_adrofs(llv)
            if isinstance(LLT, lltype.Primitive):
                return self.map_prim(llv)
            raise e

    def map_prim(self, llv):
        MuT = self.ll2mu_t.map(lltype.typeOf(llv))
        if isinstance(llv, TotalOrderSymbolic):
            llv = llv.compute_fn()
        elif isinstance(llv, CDefinedIntSymbolic):
            if llv.default == '?':
                raise IgnoredLLVal
            llv = llv.default
        elif isinstance(llv, (str, unicode)):
            assert len(llv) == 1  # char
            llv = ord(llv)
        elif isinstance(llv, rffi.CConstant):
            from pypy.module._minimal_curses.fficurses import ERR, OK
            if llv in (ERR, OK):
                llv = -1 if llv is ERR else 0
            else:
                raise NotImplementedError("Don't know how to map primitive value %s" % llv)

        return MuT._get_val_type(llv)

    def map_arrfix(self, llv):
        MuT = self.ll2mu_t.map(lltype.typeOf(llv))
        arr = mutype._muarray(MuT)
        for i in range(llv.getlength()):
            arr[i] = self.map(llv.getitem(i))
        return arr

    def map_stt(self, llv, building=False):
        LLT = lltype.typeOf(llv)
        topstt = llv._normalizedcontainer()
        if building:
            MuT = self.ll2mu_t.map(LLT)
            stt = mutype._mustruct(MuT)
            self._val_cache[(LLT, llv)] = stt

            gcidfld, gcidfld_T = self.ll2mu_t.GC_IDHASH_FLD

            if len(llv._TYPE._names) != 0:  # origional value struct is non-empty
                for fld in filter(lambda n: n != gcidfld, MuT._names):
                    setattr(stt, fld, self.map(getattr(llv, fld), building=True))

            if hasattr(stt, gcidfld) and hasattr(topstt, '_hash_cache_'):
                _idhash = topstt._hash_cache_
                setattr(stt, gcidfld, gcidfld_T._get_val_type(_idhash))

            llprnt = llv._parentstructure()
            llprnt_t = lltype.typeOf(llprnt)
            if llprnt and isinstance(llprnt_t, lltype.Struct):
                key = (llprnt_t, llprnt)
                assert key in self._val_cache
                stt._setparent(self._val_cache[key], llv._parent_index)
        else:
            if LLT._is_varsize():
                return self.map_varstt(llv)

            if topstt not in self._topstt_map:
                # build from top
                topstt_mu = self.map(topstt, building=True)
                self._topstt_map[topstt] = topstt_mu
            else:
                topstt_mu = self._topstt_map[topstt]

            # work out the depth of parent structure
            depth = 0
            prnt = llv
            while not prnt is topstt:
                depth += 1
                prnt = prnt._parentstructure()

            # traverse down according to the depth
            stt = topstt_mu
            while depth > 0:
                depth -= 1
                stt = stt.super

        return stt

    def map_varstt(self, llv):
        LLT = lltype.typeOf(llv)
        MuT = self.ll2mu_t.map(LLT)
        arr = getattr(llv, LLT._arrayfld)
        hyb = mutype._muhybrid(MuT, MuT.length(arr.getlength()))

        gcidfld, gcidfld_T = self.ll2mu_t.GC_IDHASH_FLD

        for fld in filter(lambda n: n != gcidfld, MuT._names[:-1]):
            setattr(hyb, fld, self.map(getattr(llv, fld)))

        if hasattr(hyb, gcidfld) and hasattr(llv, '_hash_cache_'):
            _idhash = llv._hash_cache_
            setattr(hyb, gcidfld, gcidfld_T._get_val_type(_idhash))

        _memarr = getattr(hyb, MuT._varfld)
        for i in range(arr.getlength()):
            _memarr[i] = self.map(arr.getitem(i))

        hyb.length = self.map(arr.getlength())
        return hyb

    def map_arr(self, llv):
        LLT = lltype.typeOf(llv)
        MuT = self.ll2mu_t.map(LLT)

        if llv._TYPE.OF is lltype.Void:
            stt = mutype._mustruct(MuT)
            stt.length = self.map(llv.getlength())
            return stt

        hyb = mutype._muhybrid(MuT, self.map(llv.getlength()))

        _memarr = getattr(hyb, MuT._varfld)
        for i in range(hyb.length.val):
            _memarr[i] = self.map(llv.getitem(i))

        return hyb

    def map_ptr(self, llv):
        LLT = lltype.typeOf(llv)
        MuT = self.ll2mu_t.map(LLT)
        refcls = MuT._val_type

        if llv._obj0 is None:
            return refcls._null(MuT)

        if isinstance(LLT.TO, lltype.FuncType):
            return self.map_funcptr(llv)

        if MuT.TO is mutype.MU_VOID:
            muv = refcls._null(MuT)
            log.warning("Translating LL value '%(llv)r' to '%(muv)r'" % locals())
            return muv

        ref = refcls._null(MuT)     # set object later

        self._todoptrs.append((llv._obj, ref))
        return ref

    def resolve_ptrs(self):
        for llv, ref in self._todoptrs:
            obj = self.map(llv)
            ref._obj = obj

    def map_funcptr(self, llv):
        LLT = lltype.typeOf(llv)
        MuT = self.ll2mu_t.map(LLT)
        fnc = llv._obj
        graph = getattr(fnc, 'graph', None)
        if graph:
            return mutype._mufuncref(MuT, graph=graph,
                                     _name=getattr(fnc, '_name', ''))
        else:
            # external functions
            Sig = MuT.Sig
            MuT = mutype.MuUFuncPtr(Sig)
            c_name = fnc._name
            return mutype._muufuncptr(MuT, _name=c_name, eci=fnc.compilation_info)

    def map_adrofs(self, llv):
        def rec(llv):
            if isinstance(llv, llmemory.CompositeOffset):
                ofs = 0
                for llv2 in llv.offsets:
                    ofs += rec(llv2)
                return ofs
            elif isinstance(llv, llmemory.ItemOffset):
                MuT = mutype.MuArray(self.ll2mu_t.map(llv.TYPE), llv.repeat)
                return layout.mu_offsetOf(MuT, llv.repeat)
            elif isinstance(llv, llmemory.FieldOffset):
                MuT = self.ll2mu_t.map(llv.TYPE)
                if isinstance(MuT, mutype.MuHybrid) and \
                                llv.fldname == MuT._varfld and len(MuT._names) > 1:
                    # get the offset of the 'length' field instead of variable part
                    return layout.mu_offsetOf(MuT, MuT._names[-2])
                return layout.mu_offsetOf(MuT, llv.fldname)
            elif isinstance(llv, llmemory.ArrayItemsOffset):
                MuT = self.ll2mu_t.map(llv.TYPE)
                _ofs = 8 if self.ll2mu_t.GC_IDHASH_FLD[0] in MuT._names else 0  # __gc_idhash field
                if llv.TYPE._hints.get("nolength", False):
                    return _ofs
                return _ofs + 8  # sizeof(i64)
            else:
                raise AssertionError("Value {:r} of type {:r} shouldn't appear.".format(llv, type(llv)))
        MuT = self.ll2mu_t.map(lltype.typeOf(llv))
        return MuT._get_val_type()(rec(llv))

    def map_opq(self, llv):
        if llv._TYPE is lltype.RuntimeTypeInfo:
            # Since rtti is of char type in C, we use mu_int8 here as well, with an initialised 0 value
            return mutype.mu_int8(randint(0, 0xff))

        if hasattr(llv, 'container'):
            container = llv._normalizedcontainer()
            muv = self.map(container)
            # log.ll2mu_val("%(llv)r really is %(muv)r" % locals())
            return muv

        muv = mutype.mu_int64(randint(0, 0xffffffff))  # randomise it.
        log.ll2mu_val("WARNING: specialising '%r' to '%r' of type '%s'." % (llv, muv, muv._TYPE))
        return muv

    def map_wref(self, llv):
        MuT = self.ll2mu_t.map(lltype.typeOf(llv))
        stt = mutype._mustruct(MuT)
        llobj = llv._dereference()
        muobj = self.map(llobj) if llobj else MuT._null(MuT)
        setattr(stt, 'wref', muobj)
        return stt
