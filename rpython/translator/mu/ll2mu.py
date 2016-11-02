from rpython.rtyper.lltypesystem import lltype, llmemory, rffi
from rpython.translator.mu import mutype, layout
from rpython.rtyper.normalizecalls import TotalOrderSymbolic
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
        "cast_int_to_uint",
        "cast_uint_to_int",
        "cast_int_to_unichar",
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

    def __init__(self):
        self._type_cache = {}
        self._pending_ptr_types = []
        self._name_cache = {}
        self._val_cache = {}
        self._ptr_cache = {}
        self._topstt_map = {}
        self._pending_ptr_values = []

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
        return mutype.MU_INT64  # all Address types are mapped to int<64>

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
        for i in range(hyb.length.val):
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
            return mutype._muufuncptr(MuT, _name=c_name, eci=fnc.compilation_info)

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

    def var(self, name, MuT):
        v = Variable(name)
        v.concretetype = MuT
        return v

    def map_op(self, llop):
        """
        May RTyped operations to Mu operations.
        NOTE: the name of the original operation is changed.

        :param llop: SpaceOperation
        :return: [SpaceOperation]
        """
        try:
            return getattr(self, 'map_op_' + llop.opname)(llop)
        except AttributeError:
            if llop.opname in IgnoredLLOp._llops:  # Making ignoring explicit
                raise IgnoredLLOp(llop.opname)

            if llop.opname in _binop_map:   # a binop
                if any(cmpop in llop.opname for cmpop in 'lt le eq ne ge gt'.split(' ')):
                    return self._map_cmpop(llop)
                else:
                    return self._map_binop(llop)

            raise NotImplementedError("Has not implemented specialisation for operation '%s'" % llop)

    def dest_clause(self, blk, args):
        """ Destination clause is a Link """
        return Link(args, blk)

    def exc_clause(self, dst_nor, dst_exc):
        """ Exception clause is a tuple """
        return dst_nor, dst_exc

    # ----------------
    # call ops
    def map_op_direct_call(self, llop):
        fr = llop.args[0].value
        if isinstance(fr, mutype._muufuncptr):  # external function
            opname = 'mu_ccall'
        else:
            opname = 'mu_call'

        llop.opname = opname
        return [llop]

    def map_op_indirect_call(self, llop):
        last = llop.args[-1]
        if isinstance(last, Constant) and isinstance(last.value, list):
            args = llop.args[:-1]
        else:
            args = llop.args
        llop.opname = 'mu_call'
        llop.args = args
        return [llop]

    # ----------------
    # primitive ops
    def map_op_bool_not(self, llop):
        ops = []
        if llop.args[0].concretetype is mutype.MU_INT1:
            res = self.var('res', mutype.MU_INT8)
            v = ops.append(SpaceOperation('mu_convop', [
                self.mapped_const(rmu.MuConvOptr.ZEXT),
                llop.args[0],
                self.mapped_const(mutype.MU_INT8),
            ],
                                          res))
        else:
            v = llop.args[0]
        SpaceOperation.__init__(llop, 'mu_binop', [
            self.mapped_const(rmu.MuBinOptr.XOR),
            v,
            self.mapped_const(True),
            self.mapped_const({})
        ],
                                llop.result)
        ops.append(llop)
        return ops

    def map_op_int_is_true(self, llop):
        cmp_res = self.var('cmp_res', mutype.MU_INT1)
        SpaceOperation.__init__(llop, 'mu_select', [
            cmp_res,
            self.mapped_const(True),
            self.mapped_const(False)
        ],
                                llop.result)
        return [llop]
    map_op_uint_is_true = map_op_int_is_true
    map_op_llong_is_true = map_op_int_is_true
    map_op_ullong_is_true = map_op_int_is_true
    map_op_lllong_is_true = map_op_int_is_true

    def map_op_int_neg(self, llop):
        MuT = llop.args[0].concretetype
        SpaceOperation.__init__(llop, 'int_sub', [
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
        neg_x = self.var('neg_x', x.concretetype)
        op_neg = SpaceOperation('int_neg', [x], neg_x)
        ops.extend(self.map_op(op_neg))
        # x > 0 ?
        cmp_res = self.var('cmp_res', mutype.MU_INT1)
        op_cmp = SpaceOperation('mu_cmpop', [
            self.mapped_const(rmu.MuCmpOptr.SGT),
            x, Constant(MuT._val_type(0), MuT)
        ],
                                cmp_res)
        ops.append(op_cmp)
        # True -> x, False -> -x
        SpaceOperation.__init__(llop, 'mu_select', [cmp_res, x, neg_x], llop.result)
        ops.append(llop)

        return [op_neg, op_cmp, llop]

    map_op_llong_abs = map_op_int_abs
    map_op_lllong_abs = map_op_int_abs

    def map_op_int_invert(self, llop):
        # 2's complement
        # x' = (-x) - 1
        ops = []
        x = llop.args[0]

        neg_x = self.var('neg_x', x.concretetype)
        op_neg = SpaceOperation('int_neg', [x], neg_x)
        ops.extend(self.map_op(op_neg))

    map_op_uint_invert = map_op_int_invert
    map_op_llong_invert = map_op_int_invert
    map_op_ullong_invert = map_op_int_invert
    map_op_lllong_invert = map_op_int_invert

    def map_op_int_between(self, llop):
        muops = []
        ge_res = self.var('ge_res', mutype.MU_INT8)
        lt_res = self.var('lt_res', mutype.MU_INT8)
        op_ge = SpaceOperation('int_ge', [llop.args[1], llop.args[0]], ge_res)
        muops.extend(self.map_op(op_ge))
        op_lt = SpaceOperation('int_lt', [llop.args[1], llop.args[2]], lt_res)
        muops.extend(self.map_op(op_lt))
        SpaceOperation.__init__(llop, 'int_and', [ge_res, lt_res], llop.result)
        muops.extend(self.map_op(llop))
        return muops

    def map_op_int_force_ge_zero(self, llop):
        muops = []
        a = llop.args[0]
        MuT = a.concretetype
        zero = Constant(MuT._val_type(0), MuT)
        lt_zero = self.var('lt_zero', mutype.MU_INT1)
        op_cmp = SpaceOperation('mu_cmpop', [
            self.map_op(rmu.MuCmpOptr.SLT),
            a, zero
        ],
                                lt_zero)
        SpaceOperation.__init__(llop, 'mu_select', [lt_zero, zero, a], llop.result)
        return [op_cmp, llop]

    def map_op_int_add_ovf(self, llop):
        flag_v = self.var('ovf_V', mutype.MU_INT1)
        flag = self.mapped_const(rmu.MuBinOpStatus.V)

        SpaceOperation.__init__(llop, 'mu_binop', [
            self.mapped_const(rmu.MuBinOptr.ADD),
            llop.args[0], llop.args[1],
            self.mapped_const({
                'status': (flag, [flag_v])
            })
        ],
                                llop.result)
        return [llop]

    map_op_int_add_nonneg_ovf = map_op_int_add_ovf

    def map_op_int_sub_ovf(self, llop):
        flag_v = self.var('ovf_V', mutype.MU_INT1)
        flag = self.mapped_const(rmu.MuBinOpStatus.V)

        SpaceOperation.__init__(llop, 'mu_binop', [
            self.mapped_const(rmu.MuBinOptr.SUB),
            llop.args[0], llop.args[1],
            self.mapped_const({
                'status': (flag, [flag_v])
            })
        ],
                                llop.result)
        return [llop]

    def map_op_int_mul_ovf(self, llop):
        flag_v = self.var('ovf_V', mutype.MU_INT1)
        flag = self.mapped_const(rmu.MuBinOpStatus.V)

        SpaceOperation.__init__(llop, 'mu_binop', [
            self.mapped_const(rmu.MuBinOptr.MUL),
            llop.args[0], llop.args[1],
            self.mapped_const({
                'status': (flag, [flag_v])
            })
        ],
                                llop.result)
        return [llop]

    def _map_binop(self, llop):
        SpaceOperation.__init__(llop, 'mu_binop', [
            self.mapped_const(_binop_map[llop.opname]),
            llop.args[0],
            llop.args[1],
            self.mapped_const({})
        ],
                                llop.result)
        return [llop]

    def _map_cmpop(self, llop):
        muops = []
        cmpres = self.var('cmpres', mutype.MU_INT1)
        muops.append(SpaceOperation('mu_cmpop', [
            self.mapped_const(_binop_map[llop.opname]),
            llop.args[0],
            llop.args[1],
        ],
                                cmpres))
        SpaceOperation.__init__(llop, 'mu_convop', [
            self.mapped_const(rmu.MuConvOptr.ZEXT),
            cmpres,
            self.mapped_const(mutype.MU_INT8)
        ],
                                llop.result)
        muops.append(llop)
        return muops

def _init_binop_map():
    __binop_map = {
        'int_add': rmu.MuBinOptr.ADD,
        'int_sub': rmu.MuBinOptr.SUB,
        'int_mul': rmu.MuBinOptr.MUL,
        'int_floordiv': rmu.MuBinOptr.SDIV,
        'int_mod': rmu.MuBinOptr.SREM,
        'int_lt': rmu.MuCmpOptr.SLT,
        'int_le': rmu.MuCmpOptr.SLE,
        'int_eq': rmu.MuCmpOptr.EQ,
        'int_ne': rmu.MuCmpOptr.NE,
        'int_gt': rmu.MuCmpOptr.SGT,
        'int_ge': rmu.MuCmpOptr.SGE,
        'int_and': rmu.MuBinOptr.AND,
        'int_or': rmu.MuBinOptr.OR,
        'int_lshift': rmu.MuBinOptr.SHL,
        'int_rshift': rmu.MuBinOptr.ASHR,
        'int_xor': rmu.MuBinOptr.XOR,

        'uint_add': rmu.MuBinOptr.ADD,
        'uint_sub': rmu.MuBinOptr.SUB,
        'uint_mul': rmu.MuBinOptr.MUL,
        'uint_floordiv': rmu.MuBinOptr.UDIV,
        'uint_mod': rmu.MuBinOptr.UREM,
        'uint_lt': rmu.MuCmpOptr.ULT,
        'uint_le': rmu.MuCmpOptr.ULE,
        'uint_eq': rmu.MuCmpOptr.EQ,
        'uint_ne': rmu.MuCmpOptr.NE,
        'uint_gt': rmu.MuCmpOptr.UGT,
        'uint_ge': rmu.MuCmpOptr.UGE,
        'uint_and': rmu.MuBinOptr.AND,
        'uint_or': rmu.MuBinOptr.OR,
        'uint_lshift': rmu.MuBinOptr.SHL,
        'uint_rshift': rmu.MuBinOptr.LSHR,
        'uint_xor': rmu.MuBinOptr.XOR,

        'float_add': rmu.MuBinOptr.FADD,
        'float_sub': rmu.MuBinOptr.FSUB,
        'float_mul': rmu.MuBinOptr.FMUL,
        'float_truediv': rmu.MuBinOptr.FDIV,
        'float_lt': rmu.MuCmpOptr.FOLT,
        'float_le': rmu.MuCmpOptr.FOLE,
        'float_eq': rmu.MuCmpOptr.FOEQ,
        'float_ne': rmu.MuCmpOptr.FONE,
        'float_gt': rmu.MuCmpOptr.FOGT,
        'float_ge': rmu.MuCmpOptr.FOGE,
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