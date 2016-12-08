from rpython.rtyper.lltypesystem import lltype, llmemory, rffi
from rpython.translator.mu import mutype, layout
from rpython.rtyper.normalizecalls import TotalOrderSymbolic
from rpython.rtyper.annlowlevel import MixLevelHelperAnnotator
from rpython.rlib.objectmodel import CDefinedIntSymbolic
from rpython.rlib import rarithmetic, rmu
from rpython.flowspace.model import Variable, Constant, SpaceOperation, Link
from rpython.translator.c.node import needs_gcheader
from random import randint

from rpython.tool.ansi_print import AnsiLogger
from rpython.tool.ansi_mandelbrot import Driver

log = AnsiLogger("ll2mu")
mdb = Driver()

class IgnoredLLVal(NotImplementedError):
    pass

class IgnoredLLOp(NotImplementedError):
    _llops = (
        "hint",
        "likely",
        "debug_flush",
        "debug_forked",
        "debug_offset",
        "debug_print",
        "debug_start",
        "debug_stop",
        "gc_add_memory_pressure",
        "gc_set_max_heap_size",
        "gc_thread_after_fork",
        "gc_writebarrier",
        "gc_writebarrier_before_copy",
        "gc_unpin",
        "jit_conditional_call",
        "jit_force_quasi_immutable",
        "jit_force_virtual",
        "jit_is_virtual",
        "jit_marker",
    )

class LL2MuMapper:
    GC_IDHASH_FIELD = ('gc_idhash', mutype.MU_INT64)

    def __init__(self, rtyper=None):
        """
        :type mlha: rpython.rtyper.annlowlevel.MixLevelHelperAnnotator
        """
        self._type_cache = {}
        self._pending_ptr_types = []
        self._name_cache = {}
        self._val_cache = {}
        self._ptr_cache = {}
        self._topstt_map = {}
        self._pending_ptr_values = []
        if rtyper:
            self.mlha = MixLevelHelperAnnotator(rtyper)
        else:
            self.mlha = None

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
            elif isinstance(LLT, lltype.OpaqueType):
                MuT = self.map_type_opq(LLT)
            elif LLT is llmemory.WeakRef:
                MuT = self.map_wref(LLT)
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
                if hasattr(mutype, "MU_INT%d" % b):
                    return getattr(mutype, "MU_INT%d" % b)
                else:
                    return mutype.MuIntType("MU_INT%d" % b,
                                            rarithmetic.build_int('r_uint%d' % b, False, b))    # unsigned
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

        name = self._new_typename(LLT._name)
        return mutype.MuHybrid(name, *flds)

    def map_type_arr(self, LLT):
        name = "%s" % LLT.OF.__name__ \
            if hasattr(LLT.OF, '__name__') \
            else str(LLT.OF)

        if LLT.OF is lltype.Void:
            return mutype.MuStruct(name, ('length', mutype.MU_INT64))

        flds = [('items', self.map_type(LLT.OF))]
        if not LLT._hints.get('nolength', False):
            flds.insert(0, ('length', mutype.MU_INT64))

        if needs_gcheader(LLT):
            flds.insert(0, LL2MuMapper.GC_IDHASH_FIELD)

        return mutype.MuHybrid(name, *flds)

    def map_type_ptr(self, LLT):
        if isinstance(LLT.TO, lltype.FuncType):
            return self.map_type_funcptr(LLT)

        if LLT.TO._gckind == 'gc':
            cls = mutype.MuRef
        else:
            cls = mutype.MuUPtr

        MuObjT = mutype.MuForwardReference()
        self._pending_ptr_types.append((LLT.TO, MuObjT))
        return cls(MuObjT)

    def resolve_ptr_types(self):
        while len(self._pending_ptr_types) > 0:
            LLObjT, MuObjT = self._pending_ptr_types.pop()
            MuObjT.become(self.map_type(LLObjT))

    def map_type_addr(self, LLT):
        return mutype.MU_INT64  # NOTE: all Address types are mapped to int<64>

    def map_type_opq(self, LLT):
        if LLT is lltype.RuntimeTypeInfo:
            return self.map_type(lltype.Char)   # rtti is defined to be a char in C backend.

        MuT = mutype.MU_INT64   # default to int<64>
        return MuT

    def map_type_funcptr(self, LLT):
        LLFnc = LLT.TO
        ARG_TS = tuple(self.map_type(ARG) for ARG in LLFnc.ARGS if ARG != lltype.Void)
        RTN_TS = (self.map_type(LLFnc.RESULT),)
        sig = mutype.MuFuncSig(ARG_TS, RTN_TS)
        return mutype.MuFuncRef(sig)

    def map_wref(self, LLT):
        return mutype.MuStruct('WeakRef', self.GC_IDHASH_FIELD, ('wref', mutype.MU_WEAKREF_VOID))

    # -----------------------------------------------------------------------------
    def map_value(self, llv, **kwargs):
        cache, v = (self._ptr_cache, llv._obj) \
            if isinstance(llv, lltype._ptr) \
            else (self._val_cache, llv)
        LLT = lltype.typeOf(llv)
        key = (LLT, v)
        try:
            return cache[key]
        except KeyError:
            if isinstance(LLT, lltype.Primitive):
                muv = self.map_value_prim(llv)

            elif isinstance(llv, lltype._fixedsizearray):
                muv = self.map_value_arrfix(llv)

            elif isinstance(llv, lltype._struct):
                muv = self.map_value_stt(llv, **kwargs)

            elif isinstance(llv, lltype._array):
                muv = self.map_value_arr(llv)

            elif isinstance(llv, lltype._ptr):
                muv = self.map_value_ptr(llv)

            elif isinstance(llv, lltype._opaque):
                muv = self.map_value_opq(llv)

            elif isinstance(llv, llmemory._wref):
                muv = self.map_value_wref(llv)

            else:
                raise NotImplementedError(
                    "Don't know how to specialise value %r of type %r." % (llv, lltype.typeOf(llv)))

            if key not in cache:  # may have already been added to cache (in stt to prevent recursion).
                cache[key] = muv
            return muv
        except TypeError, e:
            if isinstance(llv, llmemory.AddressOffset):
                return self.map_value_adrofs(llv)
            if isinstance(LLT, lltype.Primitive):
                return self.map_value_prim(llv)
            raise e

    def map_value_prim(self, llv):
        MuT = self.map_type(lltype.typeOf(llv))
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

        return MuT._val_type(llv)

    def map_value_arrfix(self, llv):
        MuT = self.map_type(lltype.typeOf(llv))
        arr = mutype._muarray(MuT)
        for i in range(llv.getlength()):
            arr[i] = self.map_value(llv.getitem(i))
        return arr

    def map_value_stt(self, llv, building=False):
        LLT = lltype.typeOf(llv)
        topstt = llv._normalizedcontainer()
        if building:
            MuT = self.map_type(LLT)
            stt = mutype._mustruct(MuT)
            self._val_cache[(LLT, llv)] = stt

            gcidfld, gcidfld_T = self.GC_IDHASH_FIELD

            if len(llv._TYPE._names) != 0:  # origional value struct is non-empty
                for fld in filter(lambda n: n != gcidfld, MuT._names):
                    setattr(stt, fld, self.map_value(getattr(llv, fld), building=True))

            if hasattr(stt, gcidfld) and hasattr(topstt, '_hash_cache_'):
                _idhash = topstt._hash_cache_
                setattr(stt, gcidfld, gcidfld_T._val_type(_idhash))

            llprnt = llv._parentstructure()
            llprnt_t = lltype.typeOf(llprnt)
            if llprnt and isinstance(llprnt_t, lltype.Struct):
                key = (llprnt_t, llprnt)
                assert key in self._val_cache
                stt._setparentstructure(self._val_cache[key], llv._parent_index)
        else:
            if LLT._is_varsize():
                return self.map_value_varstt(llv)

            if topstt not in self._topstt_map:
                # build from top
                topstt_mu = self.map_value(topstt, building=True)
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

    def map_value_varstt(self, llv):
        LLT = lltype.typeOf(llv)
        MuT = self.map_type(LLT)
        arr = getattr(llv, LLT._arrayfld)
        hyb = mutype._muhybrid(MuT, MuT.length._val_type(arr.getlength()))

        gcidfld, gcidfld_T = self.GC_IDHASH_FIELD

        for fld in filter(lambda n: n != gcidfld and n != 'length', MuT._names[:-1]):
            setattr(hyb, fld, self.map_value(getattr(llv, fld)))

        if hasattr(hyb, gcidfld) and hasattr(llv, '_hash_cache_'):
            _idhash = llv._hash_cache_
            setattr(hyb, gcidfld, gcidfld_T._val_type(_idhash))

        _memarr = getattr(hyb, MuT._varfld)
        for i in range(arr.getlength()):
            _memarr[i] = self.map_value(arr.getitem(i))

        if hasattr(hyb, 'length'):
            hyb.length = self.map_value(arr.getlength())
        return hyb

    def map_value_arr(self, llv):
        LLT = lltype.typeOf(llv)
        MuT = self.map_type(LLT)

        if llv._TYPE.OF is lltype.Void:
            stt = mutype._mustruct(MuT)
            stt.length = self.map_value(llv.getlength())
            return stt

        hyb = mutype._muhybrid(MuT, self.map_value(llv.getlength()))

        _memarr = getattr(hyb, MuT._varfld)
        for i in range(hyb.length):
            _memarr[i] = self.map_value(llv.getitem(i))

        return hyb

    def map_value_ptr(self, llv):
        LLT = lltype.typeOf(llv)
        MuT = self.map_type(LLT)

        if llv._obj0 is None:
            return MuT._null()

        if isinstance(LLT.TO, lltype.FuncType):
            return self.map_value_funcptr(llv)

        if MuT.TO is mutype.MU_VOID:
            muv = MuT._null()
            log.warning("Translating LL value '%(llv)r' to '%(muv)r'" % locals())
            return muv

        ref = MuT._null()     # set object later

        self._pending_ptr_values.append((llv._obj, ref))
        return ref

    def resolve_ptr_values(self):
        while len(self._pending_ptr_values) > 0:
            llv, ref = self._pending_ptr_values.pop()
            obj = self.map_value(llv)
            if isinstance(ref, mutype._muref):
                ref._obj = obj  # directly set _obj in _muref
            else:
                ref._store(obj) # otherwise (iref, uptr) call _store

    def map_value_funcptr(self, llv):
        LLT = lltype.typeOf(llv)
        MuT = self.map_type(LLT)
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
            return mutype._muufuncptr(MuT, _name=c_name, eci=fnc.compilation_info, _llfnctype=LLT.TO)

    def map_value_adrofs(self, llv):
        def rec(llv):
            if isinstance(llv, llmemory.CompositeOffset):
                ofs = 0
                for llv2 in llv.offsets:
                    ofs += rec(llv2)
                return ofs
            elif isinstance(llv, llmemory.ItemOffset):
                MuT = mutype.MuArray(self.map_type(llv.TYPE), llv.repeat)
                return layout.mu_offsetOf(MuT, llv.repeat)
            elif isinstance(llv, llmemory.FieldOffset):
                MuT = self.map_type(llv.TYPE)
                if isinstance(MuT, mutype.MuHybrid) and \
                                llv.fldname == MuT._varfld and len(MuT._names) > 1:
                    # get the offset of the 'length' field instead of variable part
                    return layout.mu_offsetOf(MuT, MuT._names[-2])
                return layout.mu_offsetOf(MuT, llv.fldname)
            elif isinstance(llv, llmemory.ArrayItemsOffset):
                MuT = self.map_type(llv.TYPE)
                _ofs = 8 if self.GC_IDHASH_FIELD[0] in MuT._names else 0  # __gc_idhash field
                if llv.TYPE._hints.get("nolength", False):
                    return _ofs
                return _ofs + 8  # sizeof(i64)
            else:
                raise AssertionError("Value {:r} of type {:r} shouldn't appear.".format(llv, type(llv)))
        MuT = self.map_type(lltype.typeOf(llv))
        return MuT._val_type(rec(llv))

    def map_value_opq(self, llv):
        if llv._TYPE is lltype.RuntimeTypeInfo:
            # Since rtti is of char type in C, we use mu_int8 here as well, with an initialised 0 value
            return mutype.mu_int8(randint(0, 0xff))

        if hasattr(llv, 'container'):
            container = llv._normalizedcontainer()
            muv = self.map_value(container)
            # log.ll2mu_val("%(llv)r really is %(muv)r" % locals())
            return muv

        muv = mutype.mu_int64(randint(0, 0xffffffff))  # randomise it.
        log.ll2mu_val("WARNING: specialising '%r' to '%r' of type '%s'." % (llv, muv, muv._TYPE))
        return muv

    def map_value_wref(self, llv):
        MuT = self.map_type(lltype.typeOf(llv))
        stt = mutype._mustruct(MuT)
        llobj = llv._dereference()
        muobj = self.map_value(llobj) if llobj else MuT._null(MuT)
        setattr(stt, 'wref', muobj)
        return stt

    # -----------------------------------------------------------------------------
    def mapped_const(self, llv, LLT=None):
        if LLT is None:
            try:
                LLT = lltype.typeOf(llv)
            except TypeError:
                LLT = lltype.Void
        MuT = self.map_type(LLT)
        muv = self.map_value(llv) if LLT != lltype.Void else llv
        c = Constant(muv, MuT)
        return c

    def map_op(self, llop):
        """
        May RTyped operations to Mu operations.
        NOTE: the name of the original operation is changed.

        :param llop: SpaceOperation
        :return: [SpaceOperation]
        """
        if hasattr(self, 'map_op_' + llop.opname):
            return getattr(self, 'map_op_' + llop.opname)(llop)

        elif llop.opname in IgnoredLLOp._llops:  # Making ignoring explicit
            raise IgnoredLLOp(llop.opname)

        elif llop.opname in _binop_map:   # a binop
            if any(cmpop in llop.opname for cmpop in 'lt le eq ne ge gt'.split(' ')):
                return self._map_cmpop(llop)
            else:
                return self._map_binop(llop)
        elif llop.opname in _prim_castop_map:  # a convop
            return self._map_convop(llop)

        else:
            raise NotImplementedError("Has not implemented specialisation for operation '%s'" % llop)

    def dest_clause(self, blk, args):
        """ Destination clause is a Link """
        return Link(args, blk)

    def exc_clause(self, dst_nor, dst_exc):
        """ Exception clause is a tuple """
        return dst_nor, dst_exc

    def _same_as_false(self, llop):
        llop.__init__('same_as', [self.mapped_const(False)], llop.result)
        return [llop]

    def _same_as_true(self, llop):
        llop.__init__('same_as', [self.mapped_const(True)], llop.result)
        return [llop]

    def _rename_to_same_as(self, llop):
        llop.opname = 'same_as'
        return [llop]

    # ----------------
    # call ops
    def map_op_direct_call(self, llop):
        fr = llop.args[0].value
        if isinstance(fr, mutype._muufuncptr):  # external function
            return [self.gen_mu_ccall(llop.args[0], llop.args[1:], llop.result)]
        else:
            return [self.gen_mu_call(llop.args[0], llop.args[1:], llop.result)]

    def map_op_indirect_call(self, llop):
        last = llop.args[-1]
        if isinstance(last, Constant) and isinstance(last.value, list):
            args = llop.args[:-1]
        else:
            args = llop.args
        return [self.gen_mu_call(llop.args[0], args, llop.result)]

    # ----------------
    # primitive ops
    def map_op_bool_not(self, llop):
        ops = []
        if llop.args[0].concretetype is mutype.MU_INT1:
            ops.append(self.gen_mu_convop('ZEXT', mutype.MU_INT8, llop.args[0]))
            v = ops[-1].result
        else:
            v = llop.args[0]
        ops.append(self.gen_mu_binop('XOR', v, self.mapped_const(True), llop.result))
        return ops

    def map_op_int_is_true(self, llop):
        # x != 0
        MuT = llop.args[0].concretetype
        llop.__init__('int_ne', [llop.args[0], Constant(MuT._val_type(0), MuT)], llop.result)
        return self.map_op(llop)

    map_op_uint_is_true = map_op_int_is_true
    map_op_llong_is_true = map_op_int_is_true
    map_op_ullong_is_true = map_op_int_is_true
    map_op_lllong_is_true = map_op_int_is_true

    def map_op_int_neg(self, llop):
        MuT = llop.args[0].concretetype
        llop.__init__('int_sub', [
            Constant(MuT._val_type(0), MuT),
            llop.args[0],
        ],
                                llop.result)
        return self.map_op(llop)

    map_op_llong_neg = map_op_int_neg
    map_op_lllong_neg = map_op_int_neg

    def map_op_int_abs(self, llop):
        ops = []
        x = llop.args[0]
        MuT = x.concretetype
        # -x = 0 - x
        neg_x = varof(x.concretetype, 'neg_x')
        op_neg = SpaceOperation('int_neg', [x], neg_x)
        ops.extend(self.map_op(op_neg))
        # x > 0 ?
        cmp_res = varof(mutype.MU_INT1, 'cmp_res')
        ops.append(self.gen_mu_cmpop('SGT', x, Constant(MuT._val_type(0), MuT), cmp_res))
        # True -> x, False -> -x
        ops.append(self.gen_mu_select(cmp_res, x, neg_x, llop.result))
        return ops

    map_op_llong_abs = map_op_int_abs
    map_op_lllong_abs = map_op_int_abs

    def map_op_int_invert(self, llop):
        # 2's complement
        # x' = (-x) - 1
        ops = []
        x = llop.args[0]

        neg_x = varof(x.concretetype, 'neg_x')
        op_neg = SpaceOperation('int_neg', [x], neg_x)
        ops.extend(self.map_op(op_neg))

    map_op_uint_invert = map_op_int_invert
    map_op_llong_invert = map_op_int_invert
    map_op_ullong_invert = map_op_int_invert
    map_op_lllong_invert = map_op_int_invert

    def map_op_int_between(self, llop):
        muops = []
        ge_res = varof(mutype.MU_INT8, 'ge_res')
        lt_res = varof(mutype.MU_INT8, 'lt_res')
        op_ge = SpaceOperation('int_ge', [llop.args[1], llop.args[0]], ge_res)
        muops.extend(self.map_op(op_ge))
        op_lt = SpaceOperation('int_lt', [llop.args[1], llop.args[2]], lt_res)
        muops.extend(self.map_op(op_lt))
        llop.__init__('int_and', [ge_res, lt_res], llop.result)
        muops.extend(self.map_op(llop))
        return muops

    def map_op_int_force_ge_zero(self, llop):
        muops = []
        a = llop.args[0]
        MuT = a.concretetype
        zero = Constant(MuT._val_type(0), MuT)
        lt_zero = varof(mutype.MU_INT1, 'lt_zero')
        muops.append(self.gen_mu_cmpop('SLT', a, zero, lt_zero))
        muops.append(self.gen_mu_select(lt_zero, zero, a, llop.result))
        return muops

    def map_op_int_add_ovf(self, llop):
        flag_v = varof(mutype.MU_INT1, 'ovf_V')
        flag = 'V'
        return [self.gen_mu_binop('ADD', llop.args[0], llop.args[1], llop.result, flag, [flag_v])]

    map_op_int_add_nonneg_ovf = map_op_int_add_ovf

    def map_op_int_sub_ovf(self, llop):
        flag_v = varof(mutype.MU_INT1, 'ovf_V')
        flag = 'V'
        return [self.gen_mu_binop('SUB', llop.args[0], llop.args[1], llop.result, flag, [flag_v])]

    def map_op_int_mul_ovf(self, llop):
        flag_v = varof(mutype.MU_INT1, 'ovf_V')
        flag = 'V'
        return [self.gen_mu_binop('MUL', llop.args[0], llop.args[1], llop.result, flag, [flag_v])]

    def _map_binop(self, llop):
        return [self.gen_mu_binop(_binop_map[llop.opname], llop.args[0], llop.args[1], llop.result)]

    def _map_cmpop(self, llop):
        muops = []
        cmpres = varof(mutype.MU_INT1, 'cmpres')
        muops.append(self.gen_mu_cmpop(_binop_map[llop.opname], llop.args[0], llop.args[1], cmpres))
        muops.append(self.gen_mu_convop('ZEXT', mutype.MU_INT8, cmpres, llop.result))
        return muops

    def _map_convop(self, llop):
        return [self.gen_mu_convop(_prim_castop_map[llop.opname],
                                    llop.result.concretetype, llop.args[0], llop.result)]

    map_op_cast_int_to_uint = _rename_to_same_as
    map_op_cast_uint_to_int = _rename_to_same_as
    map_op_cast_int_to_unichar = _rename_to_same_as

    # ----------------
    # memory and pointer ops
    def map_op_malloc(self, llop):
        flavor = llop.args[-1].value['flavor']
        if flavor == 'gc':
            assert isinstance(llop.result.concretetype, mutype.MuRef)
            return [self.gen_mu_new(llop.args[0].value, llop.result)]
        else:
            assert isinstance(llop.result.concretetype, mutype.MuUPtr)
            raise NotImplementedError

    def map_op_malloc_varsize(self, llop):
        ops = []
        MuT_c, hints_c, n_c = llop.args
        MuT = MuT_c.value
        flavor = hints_c.value['flavor']
        if flavor == 'gc':
            assert isinstance(llop.result.concretetype, mutype.MuRef)
            ops.append(self.gen_mu_newhybrid(MuT, n_c, llop.result))
        else:
            assert isinstance(llop.result.concretetype, mutype.MuUPtr)
            from rpython.translator.mu import layout
            fix = layout.mu_hybsizeOf(MuT, 0)
            itm = layout.mu_hybsizeOf(MuT, 1) - fix

            # sz = fix + itm * n
            v = varof(mutype.MU_INT64)
            ops.extend(self.map_op(SpaceOperation('int_mul', [Constant(itm, mutype.MU_INT64), n_c], v)))
            sz = varof(mutype.MU_INT64, 'sz')
            ops.extend(self.map_op(SpaceOperation('int_add', [Constant(fix, mutype.MU_INT64), v], sz)))
            ops.extend(self.map_op(SpaceOperation('raw_malloc', [sz], llop.result)))

        if 'length' in MuT._names:
            ops.extend(self.map_op(SpaceOperation('setfield', [
                llop.result, Constant('length', mutype.MU_VOID), n_c
            ],
                                                  varof(mutype.MU_VOID, 'dummy'))))

        return ops

    def _getfieldiref(self, var, fldname_c):
        ops = []
        MuT = var.concretetype
        fldname = fldname_c.value
        cls = mutype.MuUPtr if isinstance(MuT, mutype.MuUPtr) else mutype.MuIRef
        if isinstance(MuT, mutype.MuRef):
            iref = varof(cls(MuT.TO), 'ir%s' % var.name)
            ops.append(self.gen_mu_getiref(var, iref))
        else:
            iref = var

        assert isinstance(MuT.TO, (mutype.MuStruct, mutype.MuHybrid))
        idx = MuT.TO._index_of(fldname)     # NOTE: may throw AttributeError
        iref_fld = varof(cls(getattr(MuT.TO, fldname)), 'irf%s_%s' % (var.name, fldname))
        ops.append(self.gen_mu_getfieldiref(iref, fldname, iref_fld))
        return iref_fld, ops

    def map_op_getfield(self, llop):
        var, fldname_c = llop.args
        try:
            iref_fld, ops = self._getfieldiref(var, fldname_c)
        except AttributeError:
            log.error("Field '%s' not found in type '%s'." % (fldname_c.value, var.concretetype.TO))
            raise IgnoredLLOp

        ops.append(self.gen_mu_load(iref_fld, llop.result))
        return ops

    def map_op_setfield(self, llop):
        var, fldname_c, val_c = llop.args
        try:
            iref_fld, ops = self._getfieldiref(var, fldname_c)
        except AttributeError:
            log.error("Field '%s' not found in type '%s'." % (fldname_c.value, var.concretetype.TO))
            raise IgnoredLLOp
        assert iref_fld.concretetype.TO == val_c.concretetype, \
            "cannot store value %s of type %s to %s" % (val_c.value, val_c.concretetype, iref_fld.concretetype)

        ops.append(self.gen_mu_store(iref_fld, val_c, llop.result))
        return ops

    def map_op_getsubstruct(self, llop):
        var, fldname_c = llop.args
        try:
            iref_fld, ops = self._getfieldiref(var, fldname_c)
        except AttributeError:
            log.error("Field '%s' not found in type '%s'." % (fldname_c.value, var.concretetype.TO))
            raise IgnoredLLOp

        if isinstance(iref_fld.concretetype.TO, (mutype.MuRef, mutype.MuUPtr)):
            ops.append(self.gen_mu_load(iref_fld, llop.result))
        return ops

    def _getarrayitemiref(self, var, idx_vc):
        ops = []
        MuT = var.concretetype
        cls = mutype.MuUPtr if isinstance(MuT, mutype.MuUPtr) else mutype.MuIRef
        if isinstance(MuT, mutype.MuRef):
            iref = varof(cls(MuT.TO), 'ir%s' % var.name)
            ops.append(self.gen_mu_getiref(var, iref))
        else:
            iref = var

        if isinstance(MuT.TO, mutype.MuHybrid):
            iref_itm0 = varof(cls(MuT.TO._vartype.OF), 'ira%s' % var.name)
            ops.append(self.gen_mu_getvarpartiref(iref, iref_itm0))
        else:
            assert isinstance(MuT.TO, mutype.MuArray)
            iref_itm0 = varof(cls(MuT.TO.OF), 'ira%s' % var.name)
            ops.extend(self.map_op(SpaceOperation('cast_pointer', [iref], iref_itm0)))

        iref_itm = varof(cls(iref_itm0.concretetype.TO), 'ir%s_itm' % var.name)
        ops.append(self.gen_mu_shiftiref(iref_itm0, idx_vc, iref_itm))
        return iref_itm, ops

    def map_op_getarrayitem(self, llop):
        var, idx_vc = llop.args
        iref_itm, ops = self._getarrayitemiref(var, idx_vc)
        ops.append(self.gen_mu_load(iref_itm, llop.result))
        return ops

    def map_op_setarrayitem(self, llop):
        var, idx_vc, val_vc = llop.args
        iref_itm, ops = self._getarrayitemiref(var, idx_vc)
        ops.append(self.gen_mu_store(iref_itm, val_vc, llop.result))
        return ops

    def map_op_getarraysubstruct(self, llop):
        _iref_itm, ops = self._getarrayitemiref(*llop.args)
        ops[-1].result = llop.result
        return ops

    def map_op_getarraysize(self, llop):
        iref_fld, ops = self._getfieldiref(llop.args[0], Constant('length', mutype.MU_VOID))
        ops.append(self.gen_mu_load(iref_fld, llop.result))
        return ops

    def _getinterioriref(self, var, offsets):
        ops = []
        MuT = var.concretetype
        cls = mutype.MuUPtr if isinstance(MuT, mutype.MuUPtr) else mutype.MuIRef
        if isinstance(MuT, mutype.MuRef):
            iref = varof(cls(MuT.TO), 'ir%s' % var.name)
            ops.append(self.gen_mu_getiref(var, iref))
        else:
            iref = var

        for o in offsets:
            if o.concretetype == mutype.MU_VOID:
                assert isinstance(o, Constant)
                assert isinstance(o.value, str)
                T = iref.concretetype.TO
                if isinstance(T, mutype.MuHybrid) and o.value == T._varfld:
                    iref_var = varof(cls(T._vartype.OF), 'ira%s' % var.name)
                    ops.append(self.gen_mu_getvarpartiref(iref, iref_var))
                    iref = iref_var
                else:
                    iref, subops = self._getfieldiref(iref, o)
                    ops.extend(subops)
            else:
                assert isinstance(o.concretetype, mutype.MuIntType)
                if len(ops) == 0 or ops[-1].opname != 'mu_getvarpartiref':
                    # This case happens when the outer container is array,
                    # and rtyper assumes it can respond to indexing.
                    # For translated hybrid type however, we need to get the variable part reference first.
                    assert isinstance(iref.concretetype.TO, mutype.MuHybrid)
                    iref_var = varof(cls(T._vartype.OF), 'ira%s' % var.name)
                    ops.append(self.gen_mu_getvarpartiref(iref, iref_var))
                    iref = iref_var
                iref_itm = varof(cls(iref.concretetype.TO), 'ir%s_itm' % var.name)
                ops.append(self.gen_mu_shiftiref(iref, o, iref_itm))
                iref = iref_itm

        return iref, ops

    def map_op_getinteriorfield(self, llop):
        var = llop.args[0]
        offsets = llop.args[1:]
        try:
            iref, ops = self._getinterioriref(var, offsets)
        except AttributeError:
            raise IgnoredLLOp

        ops.append(self.gen_mu_load(iref, llop.result))
        return ops

    def map_op_setinteriorfield(self, llop):
        var = llop.args[0]
        offsets = llop.args[1:-1]
        val_vc = llop.args[-1]
        try:
            iref, ops = self._getinterioriref(var, offsets)
        except AttributeError:
            raise IgnoredLLOp

        ops.append(self.gen_mu_store(iref, val_vc, llop.result))
        return ops

    def map_op_getinteriorarraysize(self, llop):
        iref, ops = self._getinterioriref(llop.args[0], llop.args[1:-1])
        o = llop.args[-1]
        assert o.concretetype == mutype.MU_VOID and isinstance(o.value, str)
        Hyb = iref.concretetype.TO
        assert isinstance(Hyb, mutype.MuHybrid) and o.value == Hyb._varfld

        ops.extend(self.map_op(SpaceOperation('getarraysize', [iref], llop.result)))
        return ops

    def map_op_cast_pointer(self, llop):
        if isinstance(llop.args[0], Constant) and isinstance(llop.args[0].value, mutype.MuType):
            DST = llop.args[0].value
            assert DST == llop.result.concretetype, \
                'cast destination type %s does not match result type %s' % (DST, llop.result.concretetype)
            var = llop.args[1]
        else:
            var = llop.args[0]
            DST = llop.result.concretetype

        assert var.concretetype.__class__ == llop.result.concretetype.__class__, \
            'cannot cast from %s to %s' % (var.concretetype, llop.result.concretetype)

        if isinstance(DST, (mutype.MuUPtr, mutype.MuUFuncPtr)):
            optr = 'PTRCAST'
        else:
            optr = 'REFCAST'

        return [self.gen_mu_convop(optr, DST, var, llop.result)]

    def map_op_cast_opaque_ptr(self, llop):
        llop.__init__('cast_pointer', [llop.args[0]], llop.result)
        return self.map_op_cast_pointer(llop)

    def map_op_ptr_nonzero(self, llop):
        Ptr = llop.args[0].concretetype
        NULL_c = Constant(Ptr._null(), Ptr)
        llop.__init__('ptr_ne', [llop.args[0], NULL_c], llop.result)
        return self.map_op(llop)

    def map_op_ptr_iszero(self, llop):
        Ptr = llop.args[0].concretetype
        NULL_c = Constant(Ptr._null(), Ptr)
        llop.__init__('ptr_eq', [llop.args[0], NULL_c], llop.result)
        return self.map_op(llop)

    map_op_shrink_array = _same_as_false

    # TODO: reconsider direct_ptradd and direct_arrayitems, based on the semantic in lltype
    def map_op_direct_ptradd(self, llop):
        _, ops = self._getarrayitemiref(*llop.args)
        ops[-1].result = llop.result
        return ops

    def map_op_direct_arrayitems(self, llop):
        ARRAY = llop.args[0].concretetype.TO
        if not (isinstance(ARRAY, mutype.MuArray) or mutype.mu_barebonearray(ARRAY)):
            llop.__init__('getfield', [llop.args[0], Constant('items', mutype.MU_VOID)], llop.result)
            return self.map_op(llop)
        # otherwise cast to the correct type
        llop.__init__('cast_pointer', [llop.args[0]], llop.result)
        return self.map_op_cast_pointer(llop)

    # ----------------
    # address operations
    def map_op_keepalive(self, llop):
        ref = llop.args[0]
        if isinstance(ref.concretetype, mutype.MuRef):
            return [self.gen_mu_comminst('NATIVE_UNPIN', [ref], llop.result)]
        else:
            return []

    def _map_rawmemop(self, llop):
        muops = []
        llfnp = _llrawop_c_externfncs[llop.opname[4:]]
        mufnp = self.map_value(llfnp)
        self.resolve_ptr_types()
        self.resolve_ptr_values()
        callee = Constant(mufnp, mutype.mutypeOf(mufnp))

        # out of respect for typing rigour, cast integer address to pointer
        args = llop.args
        Sig = mutype.mutypeOf(mufnp).Sig

        for i, ARG in enumerate(Sig.ARGS):
            arg = args[i]
            if arg.concretetype != ARG:
                try:
                    cast_res = varof(ARG)
                    llop_fc = SpaceOperation('force_cast', [arg], cast_res)
                    muops += self.map_op(llop_fc)
                    args[i] = cast_res
                except NotImplementedError:
                    raise TypeError("calling %(sig)s with wrong argument types (%(arg_ts)s)." % {
                        'sig': Sig,
                        'arg_ts': ', '.join(map(lambda a: a.concretetype, args))
                    })

        # correct memcpy and memmove argument order
        if mufnp._name in ('memcpy', 'memmove'):
            args = [args[1], args[0], args[2]]

        if Sig.RESULTS[0] != llop.result.concretetype:
            malloc_res = varof(Sig.RESULTS[0])
            muops.append(self.gen_mu_ccall(callee, args, malloc_res))
            llop_fc = SpaceOperation('force_cast', [malloc_res], llop.result)
            muops += self.map_op(llop_fc)
        else:
            muops.append(self.gen_mu_ccall(callee, args, llop.result))

        return muops

    map_op_raw_malloc = _map_rawmemop
    map_op_raw_free = _map_rawmemop
    map_op_raw_memset = _map_rawmemop
    map_op_raw_memcopy = _map_rawmemop
    map_op_raw_memmove = _map_rawmemop

    def map_op_free(self, llop):
        llop.opname = 'raw_free'
        return self.map_op_raw_free(llop)

    def map_op_memclear(self, llop):
        llop.__init__('raw_memset', [llop.args[0], Constant(mutype.mu_int8(0), mutype.MU_INT8), llop.args[1]], llop.result)
        return self._map_rawmemop(llop)

    def map_op_raw_load(self, llop):
        ops = []
        adr_v, ofs_c = llop.args
        assert isinstance(adr_v.concretetype, mutype.MuIntType)

        loc_adr = varof(adr_v.concretetype, 'loc_adr')
        ops.extend(self.map_op(SpaceOperation('adr_add', [adr_v, ofs_c], loc_adr)))
        PTR = mutype.MuUPtr(llop.result.concretetype)
        loc_ptr = varof(PTR, 'loc_ptr')
        ops.append(self.gen_mu_convop('PTRCAST', PTR, loc_adr, loc_ptr))
        ops.append(self.gen_mu_load(loc_ptr, llop.result))
        return ops

    def map_op_raw_store(self, llop):
        ops = []
        adr_v, ofs_c, val_vc = llop.args
        assert isinstance(adr_v.concretetype, mutype.MuIntType)

        loc_adr = varof(adr_v.concretetype, 'loc_adr')
        ops.extend(self.map_op(SpaceOperation('adr_add', [adr_v, ofs_c], loc_adr)))
        PTR = mutype.MuUPtr(llop.result.concretetype)
        loc_ptr = varof(PTR, 'loc_ptr')
        ops.append(self.gen_mu_convop('PTRCAST', PTR, loc_adr, loc_ptr))
        ops.append(self.gen_mu_store(loc_ptr, val_vc, llop.result))
        return ops

    def map_op_adr_delta(self, llop):
        llop.__init__('int_sub', llop.args, llop.result)
        return self.map_op(llop)

    def map_op_cast_ptr_to_adr(self, llop):
        ops = []
        if isinstance(llop.args[0].concretetype, mutype.MuRef):
            ptr = varof(mutype.MuUPtr(llop.args[0].concretetype.TO), 'ptr')
            ops.append(self.gen_mu_comminst('NATIVE_PIN', [llop.args[0]], ptr))
        else:
            assert isinstance(llop.args[0].concretetype, mutype.MuUPtr)
            ptr = llop.args[0]

        ops.append(self.gen_mu_convop('PTRCAST', llop.result.concretetype, ptr, llop.result))
        return ops

    def map_op_cast_ptr_to_int(self, llop):
        ops = self.map_op_cast_ptr_to_adr(llop)
        if len(ops) == 2:   # pinned
            ops.extend(self.map_op_keepalive(llop))

    def map_op_cast_adr_to_ptr(self, llop):
        assert isinstance(llop.result.concretetype, mutype.MuUPtr)
        return [self.gen_mu_convop('PTRCAST', llop.result.concretetype, llop.args[0], llop.result)]

    map_op_cast_adr_to_int = _rename_to_same_as
    map_op_cast_int_to_adr = _rename_to_same_as

    def map_op_force_cast(self, llop):
        SRC = llop.args[0].concretetype
        RES = llop.result.concretetype

        if isinstance(SRC, mutype.MuObjectRef) and isinstance(RES, mutype.MuObjectRef):
            llop.__init__('cast_pointer', [llop.args[0]], llop.result)
            return self.map_op(llop)    # does the reference class check in actual mapping function

        elif isinstance(SRC, mutype.MuObjectRef) and isinstance(RES, mutype.MuIntType):
            llop.opname = 'cast_ptr_to_adr'
            return self.map_op(llop)

        elif isinstance(SRC, mutype.MuIntType) and isinstance(RES, mutype.MuObjectRef):
            llop.opname = 'cast_adr_to_ptr'
            return self.map_op(llop)

        elif isinstance(SRC, mutype.MuIntType) and isinstance(RES, mutype.MuIntType):
            if SRC.BITS < RES.BITS:
                optr = 'ZEXT' if llop.args[0].annotation.unsigned else 'SEXT'
            else:
                optr = 'TRUNC'
            return [self.gen_mu_convop(optr, RES, llop.args[0], llop.result)]

        elif isinstance(SRC, mutype.MuFloatType) and isinstance(RES, mutype.MuIntType):
            if not ((SRC == mutype.MU_DOUBLE and RES == mutype.MU_INT64) or
                        (SRC == mutype.MU_FLOAT and RES == mutype.MU_INT32)):
                raise TypeError("wrong length when casting floating point bytes to integer: %s -> %s" % (SRC, RES))
            return [self.gen_mu_convop('BITCAST', RES, llop.args[0], llop.result)]

        elif isinstance(SRC, mutype.MuIntType) and isinstance(RES, mutype.MuFloatType):
            if not ((RES == mutype.MU_DOUBLE and SRC == mutype.MU_INT64) or
                        (RES == mutype.MU_FLOAT and SRC == mutype.MU_INT32)):
                raise TypeError("wrong length when casting integer bytes to floating point: %s -> %s" % (SRC, RES))
            return [self.gen_mu_convop('BITCAST', RES, llop.args[0], llop.result)]

        elif isinstance(SRC, mutype.MuFloatType) and isinstance(RES, mutype.MuFloatType):
            if SRC == mutype.MU_FLOAT and RES == mutype.MU_DOUBLE:
                optr = 'FPEXT'
            else:
                optr = 'FPTRUNC'
            return [self.gen_mu_convop(optr, RES, llop.args[0], llop.result)]

        elif SRC == RES:
            return self._rename_to_same_as(llop)
        else:
            raise NotImplementedError("forcecast: %s -> %s" % (SRC, RES))

    map_op_cast_primitive = map_op_force_cast

    map_op_gc_can_move = _same_as_true
    map_op_gc_pin = _same_as_true
    map_op_gc_writebarrier_before_copy = _same_as_true

    def map_op_gc_load_indexed(self, llop):
        ops = []
        buf, idx_c, scale_c, base_ofs_c, = llop.args
        adr = varof(mutype.MU_INT64)
        base_adr = varof(mutype.MU_INT64)
        ofs = varof(scale_c.concretetype)
        llops = [
            SpaceOperation('cast_ptr_to_adr', [buf], adr),
            SpaceOperation('adr_add', [adr, base_ofs_c], base_adr),
            SpaceOperation('int_mul', [idx_c, scale_c], ofs),
            SpaceOperation('raw_load', [base_adr, ofs], llop.result),
            SpaceOperation('keepalive', [buf], varof(mutype.MU_VOID)),
        ]
        for op in llops:
            ops.extend(self.map_op(op))

        return ops

    def map_op_gc_identityhash(self, llop):
        def _ll_identityhash(obj):
            from rpython.rlib.objectmodel import keepalive_until_here
            from rpython.rtyper.rclass import OBJECT
            from rpython.rtyper.lltypesystem.lloperation import llop

            # obj = lltype.cast_pointer(lltype.Ptr(OBJECT), obj)
            h = llop.mu_getgcidhash(lltype.Signed, obj)
            if h == 0:
                addr = llmemory.cast_ptr_to_adr(obj)
                addr_int = llmemory.cast_adr_to_int(addr)
                h = addr_int
                llop.mu_setgcidhash(lltype.Void, obj)
                keepalive_until_here(obj)
            return h

        callee_c = self.mlha.constfunc(_ll_identityhash, [llop.args[0].annotation], llop.result.annotation)
        self.mlha.finish()
        self.mlha.backend_optimize()
        callee_c.value = self.map_value(callee_c.value)
        callee_c.concretetype = mutype.mutypeOf(callee_c.value)

        llop.__init__('direct_call', [callee_c, llop.args[0]], llop.result)
        return self.map_op(llop)

    def map_op_mu_getgcidhash(self, llop):
        llop.__init__('getfield', [llop.args[0], Constant(self.GC_IDHASH_FIELD[0], mutype.MU_VOID)], llop.result)
        return self.map_op(llop)

    def map_op_mu_setgcidhash(self, llop):
        llop.__init__('setfield', [llop.args[0], Constant(self.GC_IDHASH_FIELD[0], mutype.MU_VOID), llop.args[1]],
                      llop.result)
        return self.map_op(llop)

    map_op_gc_id = map_op_gc_identityhash
    map_op_gc__collect = _same_as_true

    def map_op_length_of_simple_gcarray_from_opaque(self, llop):
        ops = []
        MuT = self.map_type(lltype.Ptr(lltype.GcArray(lltype.Signed)))
        self.resolve_ptr_types()
        ref = varof(MuT)
        ops.extend(self.map_op_cast_pointer(SpaceOperation('cast_pointer', [llop.args[0]], ref)))
        ops.extend(self.map_op_getarraysize(SpaceOperation('getarraysize', [ref], llop.result)))
        return ops

    def set_threadlocal_struct_type(self, TYPE):
        self.TLStt = TYPE

    def map_op_threadlocalref_get(self, llop):
        ops = []

        tlref_void = varof(mutype.MuRef(mutype.MU_VOID))
        ops.append(self.gen_mu_comminst('GET_THREADLOCAL', [], tlref_void))
        RefStt = mutype.MuRef(self.TLStt)
        tlref_stt = varof(RefStt)
        ops.extend(self.map_op(SpaceOperation('cast_pointer', [tlref_void], tlref_stt)))
        fld = llop.args[0].value.expr[10:]
        ops.extend(self.map_op(SpaceOperation('getfield', [tlref_stt, Constant(fld, mutype.MU_VOID)], llop.result)))
        return ops

    def map_op_threadlocalref_set(self, llop):
        ops = []

        tlref_void = varof(mutype.MuRef(mutype.MU_VOID))
        ops.append(self.gen_mu_comminst('GET_THREADLOCAL', [], tlref_void))
        RefStt = mutype.MuRef(self.TLStt)
        tlref_stt = varof(RefStt)
        ops.extend(self.map_op(SpaceOperation('cast_pointer', [tlref_void], tlref_stt)))
        fld = llop.args[0].value.expr[10:]
        ops.extend(self.map_op(SpaceOperation('setfield', [tlref_stt, Constant(fld, mutype.MU_VOID), llop.args[1]], llop.result)))
        return ops

    def map_op_mu_threadlocalref_init(self, llop):
        ops = []

        ops.append(self.gen_mu_new(self.TLStt))
        ref = ops[-1].result
        ops.append(self.gen_mu_comminst('SET_THREADLOCAL', [ref], varof(mutype.MU_VOID)))
        return ops

    def map_op_weakref_create(self, llop):
        ops = []

        Stt = self.map_type(llmemory.WeakRef)
        ops.append(self.gen_mu_new(Stt, llop.result))
        ops.extend(self.map_op(SpaceOperation('setfield', [llop.result, Constant('wref'), llop.args[0]],
                                              varof(mutype.MU_VOID))))
        return ops

    def map_op_weakref_deref(self, llop):
        llop.__init__('getfield', [llop.args[0], Constant('wref')], llop.result)
        return self.map_op(llop)

    # ----------------
    # Some dummy gc operations
    def map_op_gc_get_rpy_memory_usage(self, llop):
        MuT = llop.result.concretetype
        llop.__init__('same_as', [Constant(MuT._val_type(-1), MuT)], llop.result)
        return [llop]
    map_op_gc_get_rpy_type_index = map_op_gc_get_rpy_memory_usage

    map_op_gc_get_rpy_roots = _same_as_false
    map_op_gc_get_rpy_referents = _same_as_false
    map_op_gc_is_rpy_instance = _same_as_false
    map_op_gc_dump_rpy_heap = _same_as_false
    map_op_gc_thread_before_fork = _same_as_false

    map_op_gc_stack_bottom = lambda self, llop: []  # no-op


    # -----------------------------------------------------------------------------
    # helper functions for constructing muops
    def gen_mu_binop(self, optr, opnd1, opnd2, res=None, status=None, status_results=None, excclause=None):
        assert hasattr(rmu.MuBinOptr, optr)
        assert opnd1.concretetype == opnd2.concretetype
        if res:
            assert res.concretetype == opnd1.concretetype
        if status:
            assert hasattr(rmu.MuBinOpStatus, status)
            for v in status_results:
                assert isinstance(v, Variable)
                assert v.concretetype == mutype.MU_INT1

        metainfo = {}
        if status:
            metainfo['status'] = (status, status_results)
        if excclause:
            metainfo['excclause'] = excclause

        return SpaceOperation('mu_binop', [
            Constant(optr, mutype.MU_VOID),
            opnd1, opnd2,
            self.mapped_const(metainfo)
        ],
                              res if res else varof(opnd1.concretetype))

    def gen_mu_cmpop(self, optr, opnd1, opnd2, res=None):
        assert hasattr(rmu.MuCmpOptr, optr)
        assert opnd1.concretetype == opnd2.concretetype
        if res:
            assert res.concretetype == mutype.MU_INT1

        return SpaceOperation('mu_cmpop', [Constant(optr, mutype.MU_VOID), opnd1, opnd2],
                              res if res else varof(mutype.MU_INT1))

    def gen_mu_convop(self, optr, TYPE, opnd, res=None):
        assert hasattr(rmu.MuConvOptr, optr)
        if res:
            assert res.concretetype == TYPE

        return SpaceOperation('mu_convop', [
            Constant(optr, mutype.MU_VOID),
            Constant(TYPE, mutype.MU_VOID),
            opnd
        ],
                              res if res else varof(TYPE))

    def gen_mu_select(self, cond, if_true, if_false, res=None):
        assert cond.concretetype == mutype.MU_INT1
        assert if_true.concretetype == if_false.concretetype
        if res:
            assert res.concretetype == if_true.concretetype

        return SpaceOperation('mu_select', [cond, if_true, if_false],
                              res if res else varof(if_true.concretetype))

    def gen_mu_branch(self, dst, res=None):
        assert isinstance(dst, Link)
        return SpaceOperation('mu_branch', [Constant(dst, mutype.MU_VOID)], res if res else varof(mutype.MU_VOID))

    def gen_mu_branch2(self, cond, dst_true, dst_false, res=None):
        assert cond.concretetype == mutype.MU_INT1
        assert isinstance(dst_true, Link)
        assert isinstance(dst_false, Link)
        return SpaceOperation('mu_branch2', [
            cond,
            Constant(dst_true, mutype.MU_VOID),
            Constant(dst_false, mutype.MU_VOID)],
                              res if res else varof(mutype.MU_VOID))

    def gen_mu_switch(self, var, dst_default, dst_cases, res=None):
        MuT = var.concretetype
        assert isinstance(dst_default, Link)
        for case in dst_cases:
            assert isinstance(case, Link)
            assert case.exitcase.concretetype == MuT

        cases = [Constant(c, mutype.MU_VOID) for c in dst_cases]
        return SpaceOperation('mu_switch', [var, Constant(dst_default, mutype.MU_VOID)] + cases,
                              res if res else varof(mutype.MU_VOID))

    def gen_mu_call(self, callee, args, res=None, keepalive=None, excclause=None):
        assert isinstance(callee.concretetype, mutype.MuFuncRef)
        Sig = callee.concretetype.Sig
        assert len(args) == len(Sig.ARGS)
        for i, arg in enumerate(args):
            assert arg.concretetype == Sig.ARGS[i]
        if res:
            assert res.concretetype == Sig.RESULTS[0]

        metainfo = {}
        if keepalive:
            metainfo['keepalive'] = keepalive
        if excclause:
            metainfo['excclause'] = excclause

        return SpaceOperation('mu_call', [callee] + args + [Constant(metainfo, mutype.MU_VOID)],
                              res if res else varof(Sig.RESULTS[0]))

    def gen_mu_ret(self, val=None, res=None):
        return SpaceOperation('mu_ret', [val] if val else [], res if res else varof(mutype.MU_VOID))

    def gen_mu_throw(self, excobj, res=None):
        assert isinstance(excobj.concretetype, mutype.MuRef)
        return SpaceOperation('mu_throw', [excobj], res if res else varof(mutype.MU_VOID))

    def gen_mu_new(self, TYPE, res=None):
        assert not isinstance(TYPE, mutype.MuHybrid)
        if res:
            assert res.concretetype == mutype.MuRef(TYPE)
        return SpaceOperation('mu_new', [Constant(TYPE, mutype.MU_VOID)],
                              res if res else mutype.MuRef(TYPE))

    def gen_mu_newhybrid(self, TYPE, n_vc, res=None):
        assert isinstance(TYPE, mutype.MuHybrid)
        assert isinstance(n_vc.concretetype, mutype.MuIntType)
        if res:
            assert res.concretetype == mutype.MuRef(TYPE)
        return SpaceOperation('mu_newhybrid', [Constant(TYPE, mutype.MU_VOID), n_vc],
                              res if res else mutype.MuRef(TYPE))

    def gen_mu_getiref(self, ref, res=None):
        assert isinstance(ref.concretetype, mutype.MuRef)
        if res:
            assert res.concretetype == mutype.MuIRef(ref.concretetype.TO)
        return SpaceOperation('mu_getiref', [ref],
                              res if res else mutype.MuIRef(ref.concretetype.TO))

    def gen_mu_getfieldiref(self, iref, fldname, res=None):
        assert isinstance(iref.concretetype, (mutype.MuIRef, mutype.MuUPtr))
        MuT = iref.concretetype.TO
        assert fldname in MuT._names
        if isinstance(MuT, mutype.MuHybrid):
            assert fldname != MuT._varfld
        FLD = getattr(MuT, fldname)
        cls = iref.concretetype.__class__
        if res:
            assert res.concretetype == cls(FLD)

        return SpaceOperation('mu_getfieldiref', [iref, Constant(fldname, mutype.MU_VOID)],
                              res if res else varof(cls(FLD)))

    def gen_mu_getelemiref(self, iref, idx_vc, res=None):
        assert isinstance(iref.concretetype, (mutype.MuIRef, mutype.MuUPtr))
        MuT = iref.concretetype.TO
        assert isinstance(MuT, mutype.MuArray)
        assert isinstance(idx_vc.concretetype, mutype.MuIntType)
        ELM = MuT.OF
        cls = iref.concretetype.__class__
        if res:
            assert res.concretetype == cls(ELM)

        return SpaceOperation('mu_getelemiref', [iref, idx_vc],
                              res if res else varof(cls(ELM)))

    def gen_mu_shiftiref(self, iref, ofs_vc, res=None):
        assert isinstance(iref.concretetype, (mutype.MuIRef, mutype.MuUPtr))
        assert isinstance(ofs_vc.concretetype, mutype.MuIntType)
        if res:
            assert res.concretetype == iref.concretetype

        return SpaceOperation('mu_shiftiref', [iref, ofs_vc],
                              res if res else varof(iref.concretetype))

    def gen_mu_getvarpartiref(self, irefhyb, res=None):
        assert isinstance(irefhyb.concretetype, (mutype.MuIRef, mutype.MuUPtr))
        assert isinstance(irefhyb.concretetype.TO, mutype.MuHybrid)
        Hyb = irefhyb.concretetype.TO
        cls = irefhyb.concretetype.__class__
        if res:
            assert res.concretetype == cls(Hyb._vartype.OF)

        return SpaceOperation('mu_getvarpartiref', [irefhyb],
                              res if res else cls(Hyb._vartype.OF))

    def gen_mu_load(self, ref, res=None, memord='NOT_ATOMIC'):
        assert isinstance(ref.concretetype, mutype.MuObjectRef)
        if res:
            assert res.concretetype == ref.concretetype.TO
        metainfo = {'memord': memord}
        return SpaceOperation('mu_load', [ref, Constant(metainfo, mutype.MU_VOID)],
                              res if res else varof(ref.concretetype.TO))

    def gen_mu_store(self, ref, val_vc, res=None, memord='NOT_ATOMIC'):
        assert isinstance(ref.concretetype, mutype.MuObjectRef)
        assert val_vc.concretetype == ref.concretetype.TO
        metainfo = {'memord': memord}
        return SpaceOperation('mu_store', [ref, val_vc, Constant(metainfo, mutype.MU_VOID)],
                              res if res else varof(mutype.MU_VOID))

    def gen_mu_ccall(self, callee, args, res=None, keepalive=None, excclause=None,
                      callconv='DEFAULT'):
        assert isinstance(callee.concretetype, mutype.MuUFuncPtr)
        Sig = callee.concretetype.Sig
        assert len(args) == len(Sig.ARGS)
        for i, arg in enumerate(args):
            assert arg.concretetype == Sig.ARGS[i]

        metainfo = {}
        if keepalive:
            metainfo['keepalive'] = keepalive
        if excclause:
            metainfo['excclause'] = excclause
        metainfo['callconv'] = callconv

        return SpaceOperation('mu_ccall', [callee] + args + [Constant(metainfo, mutype.MU_VOID)],
                              res if res else varof(Sig.RESULTS[0]))

    def gen_mu_comminst(self, inst, args, res, flags=[], types=[], sigs=[], keepalive=None, excclause=None):
        assert hasattr(rmu.MuCommInst, inst)
        metainfo = {}
        if flags:
            metainfo['flags'] = flags
        if types:
            metainfo['types'] = types
        if sigs:
            metainfo['sigs'] = sigs
        if keepalive:
            metainfo['keepalive'] = keepalive
        if excclause:
            metainfo['excclause'] = excclause

        return SpaceOperation('mu_comminst', [Constant(inst, mutype.MU_VOID)] + args +
                              [Constant(metainfo, mutype.MU_VOID)], res)

def varof(TYPE, name=None):
    v = Variable(name)
    v.concretetype = TYPE
    return v


def _init_binop_map():
    __binop_map = {
        'int_add': 'ADD',
        'int_sub': 'SUB',
        'int_mul': 'MUL',
        'int_floordiv': 'SDIV',
        'int_mod': 'SREM',
        'int_lt': 'SLT',
        'int_le': 'SLE',
        'int_eq': 'EQ',
        'int_ne': 'NE',
        'int_gt': 'SGT',
        'int_ge': 'SGE',
        'int_and': 'AND',
        'int_or': 'OR',
        'int_lshift': 'SHL',
        'int_rshift': 'ASHR',
        'int_xor': 'XOR',

        'uint_add': 'ADD',
        'uint_sub': 'SUB',
        'uint_mul': 'MUL',
        'uint_floordiv': 'UDIV',
        'uint_mod': 'UREM',
        'uint_lt': 'ULT',
        'uint_le': 'ULE',
        'uint_eq': 'EQ',
        'uint_ne': 'NE',
        'uint_gt': 'UGT',
        'uint_ge': 'UGE',
        'uint_and': 'AND',
        'uint_or': 'OR',
        'uint_lshift': 'SHL',
        'uint_rshift': 'LSHR',
        'uint_xor': 'XOR',

        'float_add': 'FADD',
        'float_sub': 'FSUB',
        'float_mul': 'FMUL',
        'float_truediv': 'FDIV',
        'float_lt': 'FOLT',
        'float_le': 'FOLE',
        'float_eq': 'FOEQ',
        'float_ne': 'FONE',
        'float_gt': 'FOGT',
        'float_ge': 'FOGE',

        'ptr_eq': 'EQ',
        'ptr_ne': 'NE',

        'adr_add': 'ADD',
        'adr_sub': 'SUB',
        'adr_lt': 'SLT',
        'adr_le': 'SLE',
        'adr_eq': 'EQ',
        'adr_ne': 'NE',
        'adr_gt': 'SGT',
        'adr_ge': 'SGE',
    }

    for org_type, coer_type in {
        'llong': 'int',
        'ullong': 'uint',
        'lllong': 'int',
        'char': 'uint',     # it's okay to be a super set of llops
        'unichar': 'uint'
    }.items():
        for op in "add sub mul floordiv mod and or lshift rshift xor".split(' '):
            __binop_map['%(org_type)s_%(op)s' % locals()] = __binop_map['%(coer_type)s_%(op)s' % locals()]
        for cmp in 'eq ne lt le gt ge'.split(' '):
            __binop_map['%(org_type)s_%(cmp)s' % locals()] = __binop_map['%(coer_type)s_%(cmp)s' % locals()]

    return __binop_map
_binop_map = _init_binop_map()

_prim_castop_map = {
    'cast_bool_to_int': 'ZEXT',
    'cast_bool_to_uint': 'SEXT',
    'cast_bool_to_float': 'UITOFP',
    'cast_char_to_int': 'ZEXT',
    'cast_unichar_to_int': 'ZEXT',
    'cast_int_to_char': 'TRUNC',
    'cast_int_to_float': 'SITOFP',
    'cast_int_to_longlong': 'SEXT',
    'cast_uint_to_float': 'UITOFP',
    'cast_longlong_to_float': 'SITOFP',
    'cast_ulonglong_to_float': 'UITOFP',
    'cast_float_to_int': 'FPTOSI',
    'cast_float_to_uint': 'FPTOUI',
    'cast_float_to_longlong': 'FPTOSI',
    'cast_float_to_ulonglong': 'FPTOUI',
    'truncate_longlong_to_int': 'TRUNC',
    'convert_float_bytes_to_longlong': 'BITCAST',
    'convert_longlong_bytes_to_float': 'BITCAST',
}

from rpython.rlib.rposix import eci
def external(name, args, res):
    return rffi.llexternal(name, args, res, compilation_info=eci, _nowrapper=True)
c_malloc = external("malloc", [rffi.SIZE_T], rffi.VOIDP)
c_free = external("free", [rffi.VOIDP], lltype.Void)
c_memcpy = external("memcpy", [rffi.VOIDP, rffi.VOIDP, rffi.SIZE_T], lltype.Void)
c_memset = external("memset", [rffi.VOIDP, lltype.Signed, rffi.SIZE_T], lltype.Void)
c_memmove = external("memmove", [rffi.CCHARP, rffi.CCHARP, rffi.SIZE_T], lltype.Void)
_llrawop_c_externfncs = {
    "malloc": c_malloc,
    "free": c_free,
    "memset": c_memset,
    "memcpy": c_memcpy,
    "memmove": c_memmove,
}
_llrawop_c_externfncs['memcopy'] = _llrawop_c_externfncs['memcpy']
