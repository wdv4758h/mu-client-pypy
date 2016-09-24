from rpython.mutyper.muts.muentity import MuName
from rpython.rtyper.lltypesystem import lltype, llmemory, rffi
from rpython.tool.ansi_mandelbrot import Driver
from .muts import mutype
from .muts import muops
from rpython.translator.mu import mem as mumem
from rpython.rtyper.normalizecalls import TotalOrderSymbolic
from rpython.rlib.objectmodel import CDefinedIntSymbolic
from rpython.rlib.rarithmetic import _inttypes
from rpython.flowspace.model import Constant, SpaceOperation
from rpython.translator.c.node import needs_gcheader
from random import randint

from rpython.tool.ansi_print import AnsiLogger


log = AnsiLogger("ll2mu")
mdb = Driver()

# ----------------------------------------------------------
_type_cache = {}
GC_IDHASH_FLD = '__gc_idhash'

def ll2mu_ty(llt):
    """
    Map LLTS type to MuTS type.
    :param llt: LLType
    :return: MuType
    """
    try:
        return _type_cache[llt]
    except KeyError:
        if isinstance(llt, mutype.MuType):
            mut = llt
        elif llt is llmemory.Address:
            mut = _lltype2mu_addr(llt)
        elif isinstance(llt, lltype.Primitive):
            mut = _lltype2mu_prim(llt)
        elif isinstance(llt, lltype.FixedSizeArray):
            mut = _lltype2mu_arrfix(llt)
        elif isinstance(llt, lltype.Struct):
            mut = _lltype2mu_stt(llt)
        elif isinstance(llt, lltype.Array):
            mut = _lltype2mu_arr(llt)
        elif isinstance(llt, lltype.Ptr):
            mut = _lltype2mu_ptr(llt)
        elif isinstance(llt, lltype.OpaqueType):
            mut = _lltype2mu_opq(llt)
        elif llt is llmemory.WeakRef:
            mut = _lltype2mu_wref(llt)
        else:
            raise NotImplementedError("Don't know how to specialise %s using MuTS." % llt)
        _type_cache[llt] = mut
        return mut

def _lltype2mu_prim(llt):
    type_map = {
        lltype.Signed:              mutype.int32_t,
        lltype.Unsigned:            mutype.int32_t,
        lltype.SignedLongLong:      mutype.int64_t,
        lltype.UnsignedLongLong:    mutype.int64_t,
        lltype.SignedLongLongLong:  mutype.int128_t,

        lltype.Float:            mutype.double_t,
        lltype.SingleFloat:      mutype.float_t,
        lltype.LongFloat:        mutype.double_t,

        lltype.Char:             mutype.char_t,
        lltype.Bool:             mutype.bool_t,
        lltype.Void:             mutype.void_t,
        lltype.UniChar:          mutype.unichar_t,
    }
    try:
        return type_map[llt]
    except KeyError:
        if llt._type in _inttypes.values():
            return mutype.MuInt(llt._type.BITS)
        raise NotImplementedError("Don't know how to specialise %s using MuTS." % llt)


def _lltype2mu_arrfix(llt):
    return mutype.MuArray(ll2mu_ty(llt.OF), llt.length)


__name_cache = {}
def __newtypename(name):
    if name in __name_cache:
        n = __name_cache[name] + 1
    else:
        n = 0
    __name_cache[name] = n
    return "%s_%d" % (name, n)


__stt_cache = {}
def _lltype2mu_stt(llt):
    if llt._is_varsize():
        hyb = _lltype2mu_varstt(llt)
        return hyb
    else:
        try:
            return __stt_cache[llt]
        except KeyError:
            pass

        if len(llt._names) == 0:    # empty struct
            # fill a dummy 64-bit integer field.
            return mutype.MuStruct("empty", ('dummy', mutype.int64_t))

        stt = mutype.MuStruct(__newtypename(llt._name))
        __stt_cache[llt] = stt
        lst = []

        if needs_gcheader(llt):
            lst.append((GC_IDHASH_FLD, mutype.int64_t))

        for n in llt._names:
            t_mu = ll2mu_ty(llt._flds[n])
            # if not (t_mu is mutype.void_t or (isinstance(t_mu, mutype.MuRef) and t_mu.TO is mutype.void_t)):
            if t_mu is not mutype.void_t:
                lst.append((n, t_mu))
        stt._setfields(lst)
        # stt._update_name()
        return stt


def _lltype2mu_varstt(llt):
    var_t = ll2mu_ty(llt._flds[llt._arrayfld].OF)
    if 'length' not in llt._names:
        names = list(llt._names)
        names.insert(-1, 'length')
        flds = llt._flds.copy()
        flds['length'] = lltype.Signed
    else:
        names = llt._names
        flds = llt._flds

    _flds = [(n, ll2mu_ty(flds[n])) for n in names[:-1]] + [(llt._arrayfld, var_t)]
    if needs_gcheader(llt):
        _flds.insert(0, (GC_IDHASH_FLD, mutype.int64_t))

    return mutype.MuHybrid(__newtypename(llt._name), *_flds)


def _lltype2mu_arr(llt):
    if llt.OF is lltype.Void:
        return mutype.MuStruct(__newtypename("%s" % llt.OF.__name__), ('length', mutype.int64_t))
    if llt._hints.get('nolength', False):
        flds = ('items', ll2mu_ty(llt.OF)),
    else:
        flds = ('length', mutype.int64_t), ('items', ll2mu_ty(llt.OF))

    if needs_gcheader(llt):
        flds = ((GC_IDHASH_FLD, mutype.int64_t), ) + flds

    return mutype.MuHybrid(__newtypename("%s" % llt.OF.__name__ if hasattr(llt.OF, '__name__') else str(llt.OF)), *flds)


def _lltype2mu_ptr(llt):
    if isinstance(llt.TO, lltype.FuncType):
        return _lltype2mu_funcptr(llt)
    if llt.TO._gckind == 'gc':
        cls = mutype.MuRef
    else:
        cls = mutype.MuUPtr
    return cls(ll2mu_ty(llt.TO))


def _lltype2mu_funcptr(llt):
    llfnc_t = llt.TO
    arg_ts = tuple([ll2mu_ty(arg) for arg in llfnc_t.ARGS if arg != lltype.Void])
    rtn_t = (ll2mu_ty(llfnc_t.RESULT), )
    sig = mutype.MuFuncSig(arg_ts, rtn_t)
    return mutype.MuFuncRef(sig)


def _lltype2mu_addr(llt):
    # return mutype.MuUPtr(mutype.void_t)     # all Address types are translated into uptr<void>
    return mutype.int64_t           # Assume Addresses are 64 bit.


def _lltype2mu_opq(llt):
    if llt is lltype.RuntimeTypeInfo:
        return ll2mu_ty(lltype.Char)  # rtti is defined to be a char in C backend.

    mut = mutype.int64_t  # values of opaque type are translated to be 64-bit integers
    log.warning("mapping type %r -> %r" % (llt, mut))
    return mut


def _lltype2mu_wref(llt):
    return mutype.MuStruct('WeakRef', (GC_IDHASH_FLD, mutype.int64_t), ('wref', mutype.wrefvoid_t))


# ----------------------------------------------------------
class IgnoredLLVal(NotImplementedError):
    pass

__ll2muval_cache = {}
__ll2muval_cache_ptr = {}


def ll2mu_val(llv, **kwargs):
    if isinstance(llv, mutype._muobject):
        return llv
    # if isinstance(llv, CDefinedIntSymbolic):
    #     llv = llv.default
    # elif isinstance(llv, TotalOrderSymbolic):
    #     llv = llv.compute_fn()
    # elif isinstance(llv, ItemOffset):
    #     llv = mumem.mu_sizeOf(ll2mu_ty(llv.TYPE))

    cache, v = (__ll2muval_cache_ptr, llv._obj) if isinstance(llv, lltype._ptr) else (__ll2muval_cache, llv)
    key = (lltype.typeOf(llv), v)
    try:
        return cache[key]
    except KeyError:
        llt = lltype.typeOf(llv)
        if isinstance(llv, llmemory.AddressOffset):
            muv = _llval2mu_adrofs(llv)

        elif isinstance(llt, lltype.Primitive):
            muv = _llval2mu_prim(llv)

        elif isinstance(llv, lltype._fixedsizearray):
            muv = _llval2mu_arrfix(llv)

        elif isinstance(llv, lltype._struct):
            muv = _llval2mu_stt(llv, **kwargs)

        elif isinstance(llv, lltype._array):
            muv = _llval2mu_arr(llv)

        elif isinstance(llv, lltype._ptr):
            muv = _llval2mu_ptr(llv)

        elif isinstance(llv, lltype._opaque):
            muv = _llval2mu_opq(llv)

        elif isinstance(llv, llmemory._wref):
            muv = _llval2mu_wref(llv)

        else:
            raise NotImplementedError("Don't know how to specialise value %r of type %r." % (llv, lltype.typeOf(llv)))
        
        if key not in cache:    # may have already been added to cache (in stt to prevent recursion).
            cache[key] = muv
        return muv
    except TypeError, e:
        if isinstance(llv, llmemory.AddressOffset):
            return _llval2mu_adrofs(llv)
        llt = lltype.typeOf(llv)
        if isinstance(llt, lltype.Primitive):
            return _llval2mu_prim(llv)
        raise e


def _llval2mu_prim(llv):
    mut = ll2mu_ty(lltype.typeOf(llv))
    if isinstance(llv, TotalOrderSymbolic):
        llv = llv.compute_fn()
    elif isinstance(llv, CDefinedIntSymbolic):
        if llv.default == '?':
            raise IgnoredLLVal
        llv = llv.default
    elif isinstance(llv, (str, unicode)):
        assert len(llv) == 1    # char
        llv = ord(llv)
    elif isinstance(llv, rffi.CConstant):
        from pypy.module._minimal_curses.fficurses import ERR, OK
        assert llv in (ERR, OK)
        llv = -1 if llv is ERR else 0

    return mutype._muprimitive(mut, llv)


def _llval2mu_arrfix(llv):
    mut = ll2mu_ty(llv._TYPE)
    arr = mutype._muarray(mut)
    for i in range(llv.getlength()):
        arr[i] = ll2mu_val(llv.getitem(i))

    return arr

__topstt_map = {}
def _llval2mu_stt(llv, building=False):
    if llv._TYPE._arrayfld:
        return _llval2mu_varstt(llv)

    topstt = llv._normalizedcontainer()
    if building:
        llt = lltype.typeOf(llv)
        mut = ll2mu_ty(llt)
        stt = mutype._mustruct(mut)
        __ll2muval_cache[(llt, llv)] = stt

        if len(llv._TYPE._names) != 0:  # origional value struct is non-empty
            for fld in filter(lambda n: n != GC_IDHASH_FLD, mut._names):
                setattr(stt, fld, ll2mu_val(getattr(llv, fld), building=True))

        if hasattr(stt, GC_IDHASH_FLD) and hasattr(topstt, '_hash_cache_'):
            _idhash = topstt._hash_cache_
            setattr(stt, GC_IDHASH_FLD, mutype.int64_t(_idhash))

        llprnt = llv._parentstructure()
        llprnt_t = lltype.typeOf(llprnt)
        if llprnt and isinstance(llprnt_t, lltype.Struct):
            key = (llprnt_t, llprnt)
            assert key in __ll2muval_cache
            stt._setparent(__ll2muval_cache[key], llv._parent_index)
    else:
        if topstt not in __topstt_map:
            # build from top
            topstt_mu = _llval2mu_stt(topstt, building=True)
            __topstt_map[topstt] = topstt_mu
        else:
            topstt_mu = __topstt_map[topstt]

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


def _llval2mu_varstt(llv):
    mut = ll2mu_ty(llv._TYPE)
    arr = getattr(llv, llv._TYPE._arrayfld)
    hyb = mutype._muhybrid(mut, mut.length(arr.getlength()))

    for fld in filter(lambda n: n != GC_IDHASH_FLD, llv._TYPE._names[:-1]):
        setattr(hyb, fld, ll2mu_val(getattr(llv, fld)))

    for i in range(arr.getlength()):
        getattr(hyb, mut._varfld)[i] = ll2mu_val(arr.getitem(i))

    hyb.length = ll2mu_val(arr.getlength())

    return hyb


def _llval2mu_arr(llv):
    mut = ll2mu_ty(llv._TYPE)
    if llv._TYPE.OF is lltype.Void:
        stt = mutype._mustruct(mut)
        stt.length = ll2mu_val(llv.getlength())
        return stt
    else:
        hyb = mutype._muhybrid(mut, ll2mu_val(llv.getlength()))
        var = hyb[-1]
        for i in range(hyb.length.val):
            var[i] = ll2mu_val(llv.getitem(i))

        return hyb

__todorefs = []
def _llval2mu_ptr(llv):
    is_uptr = llv._T._gckind == 'raw'
    null_cls = mutype._munullptr if is_uptr else mutype._munullref
    cls = mutype._muuptr if is_uptr else mutype._muref
    if llv._obj0 is None:
        return null_cls(ll2mu_ty(llv._TYPE))
    if isinstance(llv._TYPE.TO, lltype.FuncType):
        return _llval2mu_funcptr(llv)
    mut = ll2mu_ty(llv._TYPE)

    if mut.TO is mutype.void_t:
        muv = null_cls(mut)
        log.warning("Translating LL value '%(llv)r' to '%(muv)r'" % locals())
        return muv

    muref = mutype._muuptr(mut)
    __todorefs.append((llv._obj, muref))
    return muref


def resolve_refobjs():
    log.resolve_refobjs("Resolving all reference objects...")
    for llv, muref in __todorefs:
        muref.setobj(ll2mu_val(llv))
        mdb.dot()

__externfnc_namectr = {}
def _llval2mu_funcptr(llv):
    mut = ll2mu_ty(llv._TYPE)
    fnc = llv._obj
    graph = getattr(fnc, 'graph', None)
    if graph:
        return mutype._mufuncref(mut, graph=graph, fncname=getattr(fnc, '_name', ''))
    else:
        def _getname(c_name):
            # add a prefix to external functions so not to conflict with defined functions
            # (one instance is 'read')
            prefix = '_pypymu_cextfnc_'

            # use a counter to distinguish external functions that
            # have variable length arguments and hence
            # have different static signature
            # e.g. see pypy.module.fcntl.interp_fcntl.ioctl_int
            nd = __externfnc_namectr
            if c_name in nd:
                nd[c_name] += 1
                return prefix + "%s_%d" % (c_name, nd[c_name] - 1)
            nd[c_name] = 2

            return prefix + c_name

        # external functions
        sig = mut.Sig
        # ref2voidptr on arg_ts and rtn_t?
        # rtn_t = mutype.void_t if fnc_sig._voidrtn() else _ref2uptrvoid(fnc_sig.RTNS[0])
        # sig = mutype.MuFuncSig(map(_ref2uptrvoid, fnc_sig.ARGS), rtn_t)
        mut = mutype.MuUFuncPtr(sig)
        c_name = fnc._name
        return mutype._muexternfunc(mut, c_name, MuName(_getname(c_name)), fnc.compilation_info)

def _llval2mu_adrofs(llv):
    def rec(llv):
        if isinstance(llv, llmemory.CompositeOffset):
            ofs = 0
            for llv2 in llv.offsets:
                ofs += rec(llv2)
            return ofs
        elif isinstance(llv, llmemory.ItemOffset):
            return mumem.mu_offsetOf(mutype.MuArray(ll2mu_ty(llv.TYPE), llv.repeat), llv.repeat)
        elif isinstance(llv, llmemory.FieldOffset):
            mut = ll2mu_ty(llv.TYPE)
            if isinstance(mut, mutype.MuHybrid) and llv.fldname == mut._varfld and len(mut._names) > 1:
                # get the offset of the 'length' field instead of variable part
                return mumem.mu_offsetOf(mut, mut._names[-2])
            return mumem.mu_offsetOf(ll2mu_ty(llv.TYPE), llv.fldname)
        elif isinstance(llv, llmemory.ArrayItemsOffset):
            mut = ll2mu_ty(llv.TYPE)
            _ofs = 8 if GC_IDHASH_FLD in mut._names else 0  # __gc_idhash field
            if llv.TYPE._hints.get("nolength", False):
                return _ofs
            return _ofs + 8    # sizeof(i64)
        else:
            raise AssertionError("Value {:r} of type {:r} shouldn't appear.".format(llv, type(llv)))

    return ll2mu_ty(lltype.typeOf(llv))(rec(llv))


def _llval2mu_opq(llv):
    if llv._TYPE is lltype.RuntimeTypeInfo:
        # Since rtti is of char type in C, we use char_t here as well, with an initialised 0 value
        return mutype.char_t(randint(0, 0xff))

    if hasattr(llv, 'container'):
        container = llv._normalizedcontainer()
        muv = ll2mu_val(container)
        # log.ll2mu_val("%(llv)r really is %(muv)r" % locals())
        return muv

    muv = mutype.int64_t(randint(0, 0xffffffff))  # randomise it.
    log.ll2mu_val("WARNING: specialising '%r' to '%r' of type '%s'." % (llv, muv, muv._TYPE))
    return muv


def _llval2mu_wref(llv):
    mut = ll2mu_ty(llv._TYPE)
    stt = mutype._mustruct(mut)
    llobj = llv._dereference()
    if llobj:
        wref = ll2mu_val(llobj)
    else:
        # NULL of weakref must be of ref type.
        REF = mutype.MuRef(mut.wref.TO)
        wref = mutype._munullref(REF)
    setattr(stt, 'wref', wref)
    return stt


# ----------------------------------------------------------
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


def ll2mu_op(llop):
    tmp = _ll2mu_op(llop.opname, llop.args, llop.result)
    if isinstance(tmp, list):
        return tmp, getattr(tmp[-1], 'result', None)
    return tmp


def _ll2mu_op(opname, args, result=None):
    try:
        return globals()['_llop2mu_' + opname](*args, res=result, llopname=opname)
    except KeyError:
        if opname in IgnoredLLOp._llops:  # Making ignoring explicit
            raise IgnoredLLOp(opname)

        # try if it's an integer operation that can be redirected.
        prefixes = ('uint', 'char', 'lllong', 'long')
        if any(n in opname for n in prefixes):
            for pfx in prefixes:
                opname = opname.replace(pfx, 'int')
            try:
                return globals()['_llop2mu_' + opname](*args, res=result, llopname=opname)
            except KeyError:
                pass    # raise error on next line
        raise NotImplementedError("Has not implemented specialisation for operation '%s'" % opname)


def _newprimconst(mut, primval):
    c = Constant(mut(primval))
    c.mu_type = mut
    c.mu_name = MuName("%s_%s" % (str(c.value), c.mu_type.mu_name._name))
    return c


class _MuOpList(list):
    def append(self, op):
        list.append(self, op)
        return getattr(op, 'result', None)

    def extend(self, oplist):
        if len(oplist) > 0:
            list.extend(self, oplist)
            return getattr(self[-1], 'result', None)
        return None


# ----------------
# exception transform ops
def _llop2mu_mu_throw(exc, res=None, llopname='mu_throw'):
    return [muops.THROW(exc)]


# ----------------
# call ops
def _llop2mu_direct_call(cst_fnc, *args, **kwargs):

    ops = _MuOpList()
    fr = cst_fnc.value
    if isinstance(fr, mutype._muexternfunc):
        callee = fr
        call_op = muops.CCALL
    else:
        isinstance(fr, mutype._mufuncref)
        callee = fr.graph
        call_op = muops.CALL

    res = kwargs['res'] if 'res' in kwargs else None
    ops.append(call_op(callee, args, result=res))
    return ops


def _llop2mu_indirect_call(var_callee, *args, **kwargs):
    res = kwargs['res'] if 'res' in kwargs else None
    last = args[-1]
    if isinstance(last, Constant) and isinstance(last.value, list):
        return [muops.CALL(var_callee, args[:-1], result=res)]
    else:
        return [muops.CALL(var_callee, args, result=res)]


# ----------------
# primitive ops
def _llop2mu_bool_not(x, res=None, llopname='bool_not'):
    ops = _MuOpList()
    if x.mu_type is mutype.int1_t:
        v = ops.append(muops.ZEXT(x, mutype.bool_t))
    else:
        v = x
    ops.append(muops.XOR(v, _newprimconst(mutype.bool_t, 1), result=res))
    return ops


def _llop2mu_int_is_true(x, res=None, llopname='int_is_true'):
    ops = _MuOpList()
    cmp_res = ops.append(muops.NE(x, _newprimconst(x.mu_type, 0)))
    ops.append(muops.SELECT(cmp_res,
                            _newprimconst(mutype.bool_t, 1),
                            _newprimconst(mutype.bool_t, 0),
                            result=res))
    return ops


def _llop2mu_int_neg(x, res=None, llopname='int_neg'):
    return [muops.SUB(_newprimconst(x.mu_type, 0), x, result=res)]


def _llop2mu_int_abs(x, res=None, llopname='int_abs'):
    ops = _MuOpList()
    # -x = 0 - x
    neg_x = ops.extend(_ll2mu_op('int_neg', [x]))
    # x > 0?
    cmp_res = ops.append(muops.SGT(x, _newprimconst(x.mu_type, 0)))
    # True -> x, False -> -x
    ops.append(muops.SELECT(cmp_res, x, neg_x, result=res))
    return ops


def _llop2mu_int_invert(x, res=None, llopname='int_invert'):
    # 2's complement
    # x' = (-x) - 1
    ops = _MuOpList()
    neg_x = ops.extend(_ll2mu_op('int_neg', [x]))
    one = _newprimconst(x.mu_type, 1)
    ops.extend(_ll2mu_op('int_sub', (neg_x, one), res))
    return ops


def _llop2mu_int_between(a, x, b, res=None, llopname='int_between'):
    ops = _MuOpList()
    le_res = ops.extend(_ll2mu_op('int_le', (a, x)))
    lt_res = ops.extend(_ll2mu_op('int_lt',(x, b)))
    ops.extend(_ll2mu_op('int_and', (le_res, lt_res), res))
    return ops


def _llop2mu_int_force_ge_zero(x, res=None, llopname='int_force_ge_zero'):
    return _llop2mu_int_abs(x, res)


def _llop2mu_float_neg(x, res=None, llopname='float_neg'):
    return [muops.FSUB(_newprimconst(x.mu_type, 0.0), x, result=res)]


def _llop2mu_float_abs(x, res=None, llopname='float_abs'):
    ops = _MuOpList()
    # -x = 0 - x
    neg_x = ops.extend(_ll2mu_op('float_neg', [x]))
    # x > 0 ?
    cmp_res = ops.append(muops.FOGT(x, _newprimconst(x.mu_type, 0.0)))
    # True -> x, False -> (-x)
    ops.append(muops.SELECT(cmp_res, x, neg_x, result=res))
    return ops


def _llop2mu_float_is_true(x, res=None, llopname='float_is_true'):
    ops = _MuOpList()
    cmp_res = ops.append(muops.FUNE(x, _newprimconst(x.mu_type, 0.0)))
    ops.append(muops.SELECT(cmp_res,
                            _newprimconst(mutype.bool_t, 1),
                            _newprimconst(mutype.bool_t, 0),
                            result=res))
    return ops

__binop_map = {
    'int_floordiv':     'SDIV',
    'int_mod':          'SREM',
    'int_lshift':       'SHL',
    'int_rshift':       'ASHR',
    'uint_floordiv':    'UDIV',
    'uint_mod':         'UREM',
    'uint_lshift':      'SHL',
    'uint_rshift':      'LSHR',
    'float_add':        'FADD',
    'float_sub':        'FSUB',
    'float_mul':        'FMUL',
    'float_truediv':    'FDIV',
}

__cmpop_map = {
    'int_eq':           'EQ',
    'int_ne':           'NE',
    'unichar_eq':        'EQ',
    'unichar_ne':       'NE',
    'float_eq':         'FOEQ',
    'float_ne':         'FUNE'
}

for op in "add sub mul and or xor".split(' '):
    __binop_map['int_' + op] = op.upper()
for cmp in 'lt le gt ge'.split(' '):
    __cmpop_map['int_' + cmp] = 'S' + cmp.upper()
    __cmpop_map['uint_' + cmp] = 'U' + cmp.upper()
    __cmpop_map['float_' + cmp] = 'FO' + cmp.upper()
    __cmpop_map['char_' + cmp] = 'U' + cmp.upper()

for key in __binop_map:
    globals()['_llop2mu_' + key] = \
        lambda a, b, res, llopname: [getattr(muops, __binop_map[llopname])(a, b, result=res)]

for key in __cmpop_map:
    def __llop2mu_cmpop(a, b, res, llopname):
        ops = _MuOpList()
        cmpres = ops.append(getattr(muops, __cmpop_map[llopname])(a, b))
        ops.append(muops.SELECT(cmpres,
                                _newprimconst(mutype.bool_t, 1),
                                _newprimconst(mutype.bool_t, 0),
                                result=res))
        return ops
    globals()['_llop2mu_' + key] = __llop2mu_cmpop

_llop2mu_int_add_nonneg_ovf = lambda a, b, res, llopname: [getattr(muops, __binop_map['int_add'])(a, b, result=res)]


# ----------------
# primitive cast ops
__cast_map_pairs = {
    ('bool', 'int'): 'ZEXT',
    ('bool', 'uint'): 'SEXT',
    ('bool', 'float'): 'UITOFP',
    ('char', 'int'): 'ZEXT',
    ('unichar', 'int'): 'ZEXT',
    ('int', 'char'): 'TRUNC',
    ('int', 'float'): 'SITOFP',
    ('int', 'longlong'): 'SEXT',
    ('uint', 'float'): 'UITOFP',
    ('longlong', 'float'): 'SITOFP',
    ('ulonglong', 'float'): 'UITOFP',
    ('float', 'int'): 'FPTOSI',
    ('float', 'uint'): 'FPTOUI',
    ('float', 'longlong'): 'FPTOSI',
    ('float', 'ulonglong'): 'FPTOUI',
}
__cast_map = {}
for pair in __cast_map_pairs:
    if isinstance(pair, tuple):
        name = 'cast_%s_to_%s' % pair
        __cast_map[name] = __cast_map_pairs[pair]
        globals()['_llop2mu_' + name] = \
            lambda x, res, llopname: [getattr(muops, __cast_map[llopname])(x, res.mu_type, result=res)]

__spec_cast_map = {
    ('truncate', 'longlong', 'int'):        'TRUNC',
    ('convert', 'float_bytes', 'longlong'): 'BITCAST',
    ('convert', 'longlong_bytes', 'float'): 'BITCAST',
}

for triplet in __spec_cast_map:
    if isinstance(triplet, tuple):
        name = '%s_%s_to_%s' % triplet
        __spec_cast_map[name] = __spec_cast_map[triplet]
        del __spec_cast_map[triplet]
        globals()['_llop2mu_' + name] = \
            lambda x, res, llopname: [getattr(muops, __spec_cast_map[llopname])(x, res.mu_type, result=res)]


def _llop2mu_force_cast(x, res, llopname='force_cast'):
    SRC_MUTYPE = x.mu_type
    RES_MUTYPE = res.mu_type

    def is_unsigned(LLT):
        return LLT in (lltype.Bool, lltype.Unsigned, lltype.UnsignedLongLong) or \
               (hasattr(LLT, '_type') and LLT._type in _inttypes.values() and not LLT._type.SIGNED)

    if SRC_MUTYPE == RES_MUTYPE:
        return [], x

    if SRC_MUTYPE in (mutype.double_t, mutype.float_t) and isinstance(RES_MUTYPE, mutype.MuInt):
        # float/double -> int
        return [muops.FPTOSI(x, RES_MUTYPE, result=res)]

    elif isinstance(SRC_MUTYPE, mutype.MuInt) and RES_MUTYPE in (mutype.double_t, mutype.float_t):
        # int -> float/double
        return [muops.SITOFP(x, RES_MUTYPE, result=res)]

    elif SRC_MUTYPE is mutype.float_t and RES_MUTYPE is mutype.double_t:
        # float -> double
        return [muops.FPEXT(x, RES_MUTYPE, result=res)]

    elif SRC_MUTYPE is mutype.double_t and RES_MUTYPE is mutype.float_t:
        # double -> float
        return [muops.FPTRUNC(x, RES_MUTYPE, result=res)]

    # needs lltype
    SRC_LLTYPE = x.concretetype
    RES_LLTYPE = res.concretetype

    if isinstance(SRC_LLTYPE, lltype.Ptr) and \
            (RES_LLTYPE == llmemory.Address or isinstance(RES_LLTYPE, lltype.Primitive)):
        # Ptr -> Address/Signed
        assert SRC_LLTYPE.TO._gckind == 'raw'
        return _llop2mu_cast_ptr_to_adr(x, res)

    elif (SRC_LLTYPE == llmemory.Address or isinstance(SRC_LLTYPE, lltype.Primitive)) and \
            isinstance(RES_LLTYPE, lltype.Ptr):
        # Address/Signed -> Ptr
        assert RES_LLTYPE.TO._gckind == 'raw'
        return _llop2mu_cast_adr_to_ptr(x, res)

    elif isinstance(SRC_MUTYPE, mutype.MuInt) and isinstance(RES_MUTYPE, mutype.MuInt):
        # int -> int
        if SRC_MUTYPE.bits < RES_MUTYPE.bits:
            op = muops.ZEXT if is_unsigned(SRC_LLTYPE) else muops.SEXT
        elif SRC_MUTYPE.bits > RES_MUTYPE.bits:
            op = muops.TRUNC
        else:
            return [], x
        return [op(x, RES_MUTYPE, result=res)]

    elif isinstance(SRC_LLTYPE, lltype.Ptr) and isinstance(RES_LLTYPE, lltype.Ptr):
        # Ptr -> Ptr
        return _ll2mu_op('cast_pointer', [Constant(RES_LLTYPE), x], result=res)

    else:
        raise NotImplementedError("force_cast(%s) -> %s" % (SRC_LLTYPE, RES_LLTYPE))

_llop2mu_cast_primitive = _llop2mu_force_cast


# ----------------
# pointer operations
def _llop2mu_malloc(T, _hints, res=None, llopname='malloc'):
    flavor = _hints.value['flavor']
    if flavor == 'gc':
        return [muops.NEW(T.value, result=res)]
    else:
        cst_sz = _newprimconst(mutype.int64_t, mumem.mu_sizeOf(T.value))
        return _ll2mu_op('raw_malloc', (cst_sz,), res)


def _llop2mu_malloc_varsize(T, _hints, n, res=None, llopname='malloc_varsize'):
    ops = _MuOpList()
    flavor = _hints.value['flavor']
    if flavor == 'gc':
        mut = T.value
        if isinstance(mut, mutype.MuStruct):
            # Empty array
            obj = ops.append(muops.NEW(mut, result=res))
            return ops
        else:
            obj = ops.append(muops.NEWHYBRID(mut, n, result=res))
    else:
        # Calculate the size of memory that needs to be allocated
        # see mumem.mu_hybsizeOf for reference.

        hyb_t = T.value
        fixstt = mutype.MuStruct('fix', *[(f, getattr(hyb_t, f)) for f in hyb_t._names[:-1]])
        fix_sz = mumem.mu_sizeOf(fixstt)
        var_t = getattr(hyb_t, hyb_t._varfld)
        var_align = mumem.mu_alignOf(var_t)
        _f = mumem._alignUp(fix_sz, var_align)
        _v = mumem._alignUp(mumem.mu_sizeOf(var_t), mumem.mu_alignOf(var_t))
        # sz = f + v * n
        v = ops.extend(_ll2mu_op('int_mul', (_newprimconst(mutype.int64_t, _v), n)))
        sz = ops.extend(_ll2mu_op('int_add', (_newprimconst(mutype.int64_t, _f), v)))
        obj = ops.extend(_ll2mu_op('raw_malloc', (sz, ), res))

    # Set the length field
    try:
        _rflenfld, _ops = __getfieldiref(obj, 'length')
        ops.extend(_ops)
        ops.append(__store(_rflenfld, n))
    except KeyError:  # doesn't have a length field
        # log.malloc_varsize("Ignored setting length field in type '%s'." % obj)
        pass
    return ops


def __getfieldiref(var, fld):
    ops = _MuOpList()
    iref = var if isinstance(var.mu_type, (mutype.MuIRef, mutype.MuUPtr)) else ops.append(muops.GETIREF(var))
    mu_t = iref.mu_type.TO
    if isinstance(mu_t, mutype.MuHybrid) and fld == mu_t._varfld:
        iref_fld = ops.append(muops.GETVARPARTIREF(iref))
    else:
        try:
            idx = mu_t._index_of(fld)
            iref_fld = ops.append(muops.GETFIELDIREF(iref, idx))
        except ValueError:
            raise KeyError
    return iref_fld, ops


def _llop2mu_getsubstruct(var, cnst_fldname, res=None, llopname='getsubstruct'):
    try:
        _res, ops = __getfieldiref(var, cnst_fldname.value)
        if isinstance(_res.mu_type.TO, mutype.MuRef):
            ops.append(muops.LOAD(_res))
        if res:
            ops[-1].result = res
    except KeyError:
        log.error("Field '%s' not found in type '%s'." % (cnst_fldname.value, var.mu_type.TO))
        raise IgnoredLLOp
    return ops


def _llop2mu_getfield(var, cnst_fldname, res=None, llopname='getfield'):
    try:
        iref_fld, ops = __getfieldiref(var, cnst_fldname.value)
        ops.append(muops.LOAD(iref_fld, result=res))
    except KeyError:
        if res and res.concretetype is lltype.Void:     # trying to get a field that can't be translated.
            raise IgnoredLLOp

        log.error("Field '%s' not found in type '%s'." % (cnst_fldname.value, var.mu_type.TO))
        raise IgnoredLLOp
    return ops

def __store(iref, val):
    if isinstance(val, Constant) and isinstance(val.value, mutype._mufuncref) and hasattr(val.value, 'graph'):
        return muops.STORE(iref, val.value.graph)
    else:
        return muops.STORE(iref, val)

def _llop2mu_setfield(var, cnst_fldname, val, res=None, llopname='setfield'):
    try:
        iref_fld, ops = __getfieldiref(var, cnst_fldname.value)
        ops.append(__store(iref_fld, val))
    except KeyError:
        if val.concretetype is lltype.Void:     # trying to set a field with a value that can't be translated.
            raise IgnoredLLOp

        log.error("Field '%s' not found in type '%s'." % (cnst_fldname.value, var.mu_type.TO))
        raise IgnoredLLOp
    return ops


def __getarrayitemiref(var, idx):
    if isinstance(var.mu_type.TO, mutype.MuHybrid):
        iref_var, ops = __getfieldiref(var, var.mu_type.TO._varfld)
    else:
        assert isinstance(var.mu_type.TO, mutype.MuArray)
        ops = _MuOpList()
        iref_var = var if isinstance(var.mu_type, (mutype.MuIRef, mutype.MuUPtr)) else ops.append(muops.GETIREF(var))

    iref_itm = ops.append(muops.SHIFTIREF(iref_var, idx))
    return iref_itm, ops


def _llop2mu_getarrayitem(var, idx, res=None, llopname='getarrayitem'):
    iref_itm, ops = __getarrayitemiref(var, idx)
    ops.append(muops.LOAD(iref_itm, result=res))
    return ops


def _llop2mu_getarraysubstruct(var, idx, res=None, llopname='getarraysubstruct'):
    _iref_itm, ops = __getarrayitemiref(var, idx)
    ops[-1].result = res
    return ops


def _llop2mu_setarrayitem(var, idx, val, res=None, llopname='setarrayitem'):
    iref_itm, ops = __getarrayitemiref(var, idx)
    ops.append(__store(iref_itm, val))
    return ops


def _llop2mu_getarraysize(var, res=None, llopname='getarraysize'):
    iref_fld, ops = __getfieldiref(var, 'length')   # assuming that every Hybrid type has a length field
    ops.append(muops.LOAD(iref_fld, result=res))
    return ops


def __getinterioriref(var, offsets):
    ops = _MuOpList()
    iref = var if isinstance(var.mu_type, (mutype.MuIRef, mutype.MuUPtr)) else ops.append(muops.GETIREF(var))

    for o in offsets:
        if o.concretetype == lltype.Void:
            assert isinstance(o.value, str)
            iref, subops = __getfieldiref(iref, o.value)
            ops.extend(subops)
        else:
            assert isinstance(o.concretetype, lltype.Primitive)
            if len(ops) == 0 or ops[-1].opname != 'GETVARPARTIREF':
                # This case happens when the outer container is array,
                # and rtyper assumes it can respond to indexing.
                # For translated hybrid type however, we need to get the variable part reference first.
                assert isinstance(var.mu_type.TO, mutype.MuHybrid)
                iref = ops.append(muops.GETVARPARTIREF(iref))
            iref = ops.append(muops.SHIFTIREF(iref, o))

    return iref, ops


def _llop2mu_getinteriorfield(var, *offsets, **kwargs):
    res = kwargs['res'] if 'res' in kwargs else None
    try:
        iref, ops = __getinterioriref(var, offsets)
        ops.append(muops.LOAD(iref, result=res))
    except KeyError:
        if res and res.concretetype is lltype.Void:     # trying to get a field that can't be translated.
            raise IgnoredLLOp
        raise TypeError     # unknown type error
    return ops


def _llop2mu_setinteriorfield(var, *offsets_val, **kwards):
    offsets, val = offsets_val[:-1], offsets_val[-1]
    try:
        iref, ops = __getinterioriref(var, offsets)
        ops.append(__store(iref, val))
    except KeyError:
        if val.concretetype is lltype.Void:
            raise IgnoredLLOp
        raise TypeError     # unknown type error
    return ops


def _llop2mu_getinteriorarraysize(var, *offsets, **kwargs):
    iref, ops = __getinterioriref(var, offsets[:-1])
    o = offsets[-1]
    assert o.concretetype == lltype.Void and isinstance(o.value, str)
    hyb_t = iref.mu_type.TO if iref else var.mu_type.TO
    assert isinstance(hyb_t, mutype.MuHybrid) and o.value == hyb_t._varfld

    ops.extend(_llop2mu_getarraysize(iref, res=kwargs['res']))
    return ops


def _llop2mu_cast_pointer(cst_TYPE, var_ptr, res=None, llopname='cast_pointer'):
    if isinstance(var_ptr.mu_type, (mutype.MuUPtr, mutype.MuUFuncPtr)):
        if res:
            assert isinstance(res.mu_type, (mutype.MuUPtr, mutype.MuUFuncPtr))
        _op = muops.PTRCAST
    else:
        if res:
            assert not isinstance(res.mu_type, (mutype.MuUPtr, mutype.MuUFuncPtr))
        _op = muops.REFCAST
    return [_op(var_ptr, res.mu_type if res else cst_TYPE.value, result=res)]


def _llop2mu_cast_opaque_ptr(var_ptr, res, llopname='cast_opaque_ptr'):
    return _llop2mu_cast_pointer(Constant(ll2mu_ty(res.concretetype)), var_ptr, res)


def _llop2mu_ptr_eq(ptr1, ptr2, res=None, llopname='ptr_eq'):
    ops = _MuOpList()
    cmp_res = ops.append(muops.EQ(ptr1, ptr2))
    ops.append(muops.SELECT(cmp_res,
                            _newprimconst(mutype.bool_t, 1),
                            _newprimconst(mutype.bool_t, 0),
                            result=res))
    return ops


def _llop2mu_ptr_ne(ptr1, ptr2, res=None, llopname='ptr_eq'):
    ops = _MuOpList()
    cmp_res = ops.append(muops.NE(ptr1, ptr2))
    ops.append(muops.SELECT(cmp_res,
                            _newprimconst(mutype.bool_t, 1),
                            _newprimconst(mutype.bool_t, 0),
                            result=res))
    return ops


def _llop2mu_ptr_nonzero(ptr, res=None, llopname='ptr_nonzero'):
    cst = Constant(mutype._munullref(ptr.mu_type))
    cst.mu_type = ptr.mu_type
    cst.mu_name = MuName("%s_%s" % (str(cst.value), ptr.mu_type.mu_name._name))
    return _llop2mu_ptr_ne(ptr, cst, res)


def _llop2mu_ptr_iszero(ptr, res=None, llopname='ptr_zero'):
    cst = Constant(mutype._munullref(ptr.mu_type))
    cst.mu_type = ptr.mu_type
    cst.mu_name = MuName("%s_%s" % (str(cst.value), ptr.mu_type.mu_name._name))
    return _llop2mu_ptr_eq(ptr, cst, res)


def _llop2mu_direct_ptradd(ptr, n, res=None, llopname='direct_ptradd'):
    _, ops = __getarrayitemiref(ptr, n)
    if res:
        ops[-1].result = res
    return ops


def _llop2mu_shrink_array(ptr, sz, res=None, llopname='shrink_array'):
    return [], _newprimconst(mutype.bool_t, 0)  # always return False


def _llop2mu_direct_arrayitems(ptr, res=None, llopname='direct_arrayitems'):
    ARRAY = ptr.concretetype.TO
    from rpython.translator.c.support import barebonearray
    if not (isinstance(ARRAY, lltype.FixedSizeArray) or barebonearray(ARRAY)):
        return _ll2mu_op('getfield', [ptr, Constant('items')], result=res)
    return [], ptr


# ----------------
# address operations
def _llop2mu_keepalive(ptr, res=None, llopname='keepalive'):
    if isinstance(ptr.mu_type, mutype.MuRef):
        return [muops.NATIVE_UNPIN(ptr, result=res)]
    else:
        return [], res


from rpython.rlib.rposix import eci
def external(name, args, res):
    return rffi.llexternal(name, args, res, compilation_info=eci, _nowrapper=True)
c_malloc = external("malloc", [rffi.SIZE_T], rffi.VOIDP)
c_free = external("free", [rffi.VOIDP], lltype.Void)
c_memcpy = external("memcpy", [rffi.VOIDP, rffi.VOIDP, rffi.SIZE_T], lltype.Void)
c_memset = external("memset", [rffi.VOIDP, lltype.Signed, rffi.SIZE_T], lltype.Void)
c_memmove = external("memmove", [rffi.CCHARP, rffi.CCHARP, rffi.SIZE_T], lltype.Void)
__predef_extfns = {
    "malloc": ll2mu_val(c_malloc),
    "free": ll2mu_val(c_free),
    "memset": ll2mu_val(c_memset),
    "memcpy": ll2mu_val(c_memcpy),
    "memmove": ll2mu_val(c_memmove),
}
__predef_extfns['memcopy'] = __predef_extfns['memcpy']

def __raw2ccall(*args, **kwargs):
    ops = _MuOpList()
    fnp = __predef_extfns[kwargs['llopname'][4:]]
    sig = fnp._TYPE.Sig
    args = list(args)
    for i, arg_t in enumerate(sig.ARGS):
        if isinstance(arg_t, mutype.MuUPtr):
            args[i] = ops.append(muops.PTRCAST(args[i], mutype.MuUPtr(mutype.void_t)))    # cast to uptr<void>
    res = kwargs['res']
    if res.mu_type == mutype.void_t and len(sig.RTNS) == 1:
        res.mu_type = sig.RTNS[0]

    # Correct memcpy and memmove argument order
    if fnp.c_name in ('memcpy', 'memmove'):
        args = (args[1], args[0], args[2])
    ops.append(muops.CCALL(fnp, args, result=res))
    return ops

for op in 'malloc free memset memcopy memmove'.split(' '):
    globals()['_llop2mu_raw_' + op] = __raw2ccall


def _llop2mu_free(obj, res=None, llopname='free'):
    return _ll2mu_op('raw_free', (obj, ), res)


def _llop2mu_raw_memclear(adr, sz, res=None, llopname='raw_memclear'):
    return _ll2mu_op('raw_memset', [adr, _newprimconst(mutype.int8_t, 0), sz], result=res)


def _llop2mu_raw_load(adr, ofs, res, llopname='raw_load'):
    ops = _MuOpList()
    loc_adr = ops.extend(_ll2mu_op('adr_add', [adr, ofs]))
    loc_ptr = ops.append(muops.PTRCAST(loc_adr, mutype.MuUPtr(res.mu_type)))
    ops.append(muops.LOAD(loc_ptr, result=res))
    return ops


def _llop2mu_raw_store(adr, ofs, val, res=None, llopname='raw_store'):
    if isinstance(adr.mu_type, mutype.MuInt):
        ops = _MuOpList()
        loc_adr = ops.extend(_ll2mu_op('adr_add', [adr, ofs]))
        loc_ptr = ops.append(muops.PTRCAST(loc_adr, mutype.MuUPtr(val.mu_type)))
        ops.append(__store(loc_ptr, val))
        return ops
    elif isinstance(adr.mu_type, mutype.MuRef):
        assert isinstance(ofs.value, CDefinedIntSymbolic)
        assert ofs.value.expr.startswith("RPY_TLOFS_")  # threadlocalref_set case
        return _ll2mu_op('setfield', [adr, Constant(ofs.value.expr[10:], lltype.Void), val], result=res)


for op in "add sub lt le eq ne gt ge".split(' '):
    globals()['_llop2mu_adr_' + op] = lambda adr1, adr2, res, llopname:\
        _ll2mu_op(llopname.replace('adr', 'int'), (adr1, adr2), res)


def _llop2mu_adr_delta(adr1, adr2, res=None, llopname='adr_delta'):
    return _ll2mu_op('int_sub', (adr2, adr1), res)


def _llop2mu_cast_ptr_to_adr(ptr, res=None, llopname='cast_ptr_to_adr'):
    ops = _MuOpList()
    if isinstance(ptr.mu_type, mutype.MuUPtr):
        adr = ptr
    else:   # MuRef
        adr = ops.append(muops.NATIVE_PIN(ptr))

    ops.append(muops.PTRCAST(adr, ll2mu_ty(llmemory.Address), result=res))
    return ops


def _llop2mu_cast_ptr_to_int(ptr, res=None, llopname='cast_ptr_to_int'):
    ops = _MuOpList()
    ops.extend(_ll2mu_op('cast_ptr_to_adr', [ptr], result=res))
    if isinstance(ptr.mu_type, mutype.MuRef):
        ops.extend(_ll2mu_op('keepalive', [ptr]))
    return ops


def _llop2mu_cast_adr_to_ptr(adr, res, llopname='cast_adr_to_ptr'):
    assert isinstance(res.mu_type, mutype.MuUPtr)
    return [muops.PTRCAST(adr, res.mu_type, result=res)]


def _llop2mu_cast_adr_to_int(ptr, res=None, llopname='cast_adr_to_int'):
    return [], ptr


def _llop2mu_cast_int_to_adr(n, res=None, llopname='cast_adr_to_int'):
    return [], n


def _llop2mu_gc_can_move(ptr, res=None, llopname='gc_can_move'):
    return [], _newprimconst(mutype.bool_t, 1)


def _llop2mu_gc_pin(ptr, res=None, llopname='gc_can_move'):
    return [], _newprimconst(mutype.bool_t, 1)


def _llop2mu_gc_writebarrier_before_copy(src, dst, src_start, dst_start, length,
                                         res=None, llopname='gc_writebarrier_before_copy'):
    return [], _newprimconst(mutype.bool_t, 1)


def _llop2mu_gc_load_indexed(buf, index, scale, base_ofs, res, llopname='gc_load_indexed'):
    ops = _MuOpList()
    adr = ops.append(muops.NATIVE_PIN(buf))
    base_adr = ops.extend(_ll2mu_op('adr_add', [adr, base_ofs]))
    ofs = ops.extend(_ll2mu_op('int_mul', [index, scale]))
    ops.extend(_ll2mu_op('raw_load', [base_adr, ofs], result=res))
    ops.append(muops.NATIVE_UNPIN(buf))
    return ops


def _llop2mu_gc_identityhash(obj, res=None, llopname='gc_identityhash'):
    # assert obj.mu_type.TO._names[0] == GC_IDHASH_FLD
    # Create a function reference that has the field '_llhelper'.
    # The operation is translated into a CALL.
    # The LL helper function is caught by the mutyper for post processing,
    # and its graph will be generated by the MixedLevelHelperAnnotator.
    def _ll_identityhash(obj):
        from rpython.rlib.objectmodel import keepalive_until_here
        from rpython.rtyper.rclass import OBJECT
        # obj = lltype.cast_pointer(lltype.Ptr(OBJECT), obj)
        h = _ll_getgcidhash(obj)
        if h == 0:
            addr = llmemory.cast_ptr_to_adr(obj)
            addr_int = llmemory.cast_adr_to_int(addr)
            h = addr_int
            _ll_setgcidhash(obj, addr_int)
            keepalive_until_here(obj)
        return h

    def _ll_getgcidhash(obj):
        return 1 if obj else 0

    def _ll_setgcidhash(obj, idhash):
        return idhash * 2

    def _postproc(graph):
        from rpython.rtyper.rclass import OBJECT
        fld = Constant(GC_IDHASH_FLD, lltype.Void)
        # patch the first operation -- h_0 = direct_call((<* fn _ll_getgcidhash_...ectPtr>), obj_1)
        blk = graph.startblock
        # patch the input argument type
        blk.inputargs[0].concretetype = lltype.Ptr(OBJECT)
        idx = filter(lambda i: blk.operations[i].opname == 'direct_call', range(len(blk.operations)))[0]
        op = blk.operations[idx]
        op_repl = SpaceOperation('getfield', [op.args[1], fld], op.result)
        blk.operations[idx] = op_repl

        # patch the second operation -- v274 = direct_call((<* fn _ll_setgcidhash_...Signed>), obj_2, addr_int_0)
        blk = graph.startblock.exits[1].target
        # patch the input argument type
        blk.inputargs[0].concretetype = lltype.Ptr(OBJECT)
        idx = filter(lambda i: blk.operations[i].opname == 'direct_call', range(len(blk.operations)))[0]
        op = blk.operations[idx]
        op_repl = SpaceOperation('setfield', [op.args[1], fld, op.args[2]], op.result)
        blk.operations[idx] = op_repl

        # correct the cast_adr_to_int op args
        op = blk.operations[1]
        op.args = op.args[:1]       # throwing out the ('emulated') constant

    sig = mutype.MuFuncSig([obj.mu_type], [res.mu_type if res else mutype.int64_t])
    fnr_t = mutype.MuFuncRef(sig)
    fnr = mutype._mufuncref(fnr_t, _llhelper=_ll_identityhash, _postproc_fnc=_postproc)
    return [muops.CALL(fnr, [obj], result=res)]


def _llop2mu_gc__collect(res=None, llopname='gc__collect'):
    return [], _newprimconst(mutype.bool_t, 1)


# def _llop2mu_gc_id(obj, res=None, llopname='gc_id'):
#     ops = _MuOpList()
#     ops.extend(_ll2mu_op('cast_ptr_to_adr', [obj], result=res))
#     ops.extend(_ll2mu_op('keepalive', [obj]))
#     return ops

_llop2mu_gc_id = _llop2mu_gc_identityhash


def _llop2mu_length_of_simple_gcarray_from_opaque(opq, res=None, llopname='length_of_simple_gcarray_from_opaque'):
    ops = _MuOpList()
    mut = ll2mu_ty(lltype.Ptr(lltype.GcArray(lltype.Signed)))
    ref = ops.extend(_ll2mu_op('cast_pointer', [Constant(mut, lltype.Void), opq]))
    ops.extend(_ll2mu_op('getarraysize', [ref], result=res))
    return ops


# ----------------
# threadlocal stuff
def _llop2mu_threadlocalref_get(ofs, res=None, llopname='threadlocalref_get'):
    ops = _MuOpList()

    # HACK!
    tlstt_t = globals().get('__mu_threadlocalstt_t', None)
    assert tlstt_t

    tlref_void = ops.append(muops.GET_THREADLOCAL())
    tlref_stt = ops.extend(_ll2mu_op('cast_pointer', [Constant(mutype.MuRef(tlstt_t), mutype.void_t), tlref_void]))
    fld = ofs.value.expr[10:]
    ops.extend(_ll2mu_op('getfield', [tlref_stt, Constant(fld, lltype.Void)], result=res))
    return ops


def _llop2mu_threadlocalref_set(ofs, val, res=None, llopname='threadlocalref_set'):
    ops = _MuOpList()

    # HACK!
    tlstt_t = globals().get('__mu_threadlocalstt_t', None)
    assert tlstt_t

    tlref_void = ops.append(muops.GET_THREADLOCAL())
    tlref_stt = ops.extend(_ll2mu_op('cast_pointer', [Constant(mutype.MuRef(tlstt_t), mutype.void_t), tlref_void]))
    fld = ofs.value.expr[10:]
    ops.extend(_ll2mu_op('setfield', [tlref_stt, Constant(fld, lltype.Void), val]))
    return ops


def _llop2mu_threadlocalref_addr(res=None, llopname='threadlocalref_addr'):
    ops = _MuOpList()

    # Hack!
    tlstt_t = globals().get('__mu_threadlocalstt_t', None)
    assert tlstt_t

    tlref_void = ops.append(muops.GET_THREADLOCAL())
    reftlstt_t = mutype.MuRef(tlstt_t)
    res.mu_type = reftlstt_t
    ops.extend(_ll2mu_op('cast_pointer', [Constant(reftlstt_t, mutype.void_t), tlref_void], result=res))

    return ops


def _llop2mu_mu_threadlocalref_init(res=None, llopname='mu_threadlocalref_init'):
    ops = _MuOpList()

    # HACK!
    tlstt_t = globals().get('__mu_threadlocalstt_t', None)
    assert tlstt_t

    ref = ops.append(muops.NEW(tlstt_t))
    ops.append(muops.SET_THREADLOCAL(ref))
    return ops


def _llop2mu_mu_thread_exit(res=None, llopname='mu_thread_exit'):
    return [muops.THREAD_EXIT()]


# ----------------
# Weak references
def _llop2mu_weakref_create(ptr, res=None, llopname='weakref_create'):
    ops = _MuOpList()

    stt_t = ll2mu_ty(llmemory.WeakRef)
    ops.append(muops.NEW(stt_t, result=res))
    ops.extend(_ll2mu_op('setfield', [res, Constant('wref'), ptr]))

    return ops


def _llop2mu_weakref_deref(ptr, res=None, llopname='weakref_deref'):
    return _ll2mu_op('getfield', [ptr, Constant('wref')], result=res)


# ----------------
# Some dummy gc operations
for _llopname in ("gc_get_rpy_memory_usage", "gc_get_rpy_type_index"):
    globals()['_llop2mu_' + _llopname] = lambda res, llopname: ([], _newprimconst(res.mu_type, -1))

for _llopname in ("gc_get_rpy_roots",
                  "gc_get_rpy_referents",
                  "gc_is_rpy_instance",
                  "gc_dump_rpy_heap"):
    globals()['_llop2mu_' + _llopname] = lambda res, llopname: ([], _newprimconst(res.mu_type, 0))


def _llop2mu_gc_thread_before_fork(res=None, llopname='gc_thread_before_fork'):
    return [], _newprimconst(res.mu_type, 0)


def _llop2mu_gc_stack_bottom(res, llopname='gc_stack_bottom'):
    return [], res


# ----------------
# Other dummy operations
def _llop2mu_debug_offset(res, llopname='debug_offset'):
    return [], _newprimconst(res.mu_type, -1)

def _llop2mu_debug_fatalerror(msg, res, llopname='debug_fatalerror'):
    return [], res

def _llop2mu_have_debug_prints(res, llopname='have_debug_prints'):
    return [], _newprimconst(res.mu_type, 0)

# TODO: rest of the operations
