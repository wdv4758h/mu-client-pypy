from rpython.mutyper.muts.muentity import MuName, MuGlobalCell
from rpython.rtyper.lltypesystem import lltype
from rpython.rtyper.lltypesystem import llmemory
from rpython.rtyper.lltypesystem.llmemory import ItemOffset
from .muts import mutype
from .muts import muops
from .muts import muni
from rpython.rtyper.normalizecalls import TotalOrderSymbolic
from rpython.rlib.objectmodel import CDefinedIntSymbolic
from rpython.rlib.rarithmetic import _inttypes
from rpython.flowspace.model import Constant

import py
from rpython.tool.ansi_print import ansi_log


log = py.log.Producer("ll2mu")
py.log.setconsumer("ll2mu", ansi_log)


# ----------------------------------------------------------
def ll2mu_ty(llt):
    """
    Map LLTS type to MuTS type.
    :param llt: LLType
    :return: MuType
    """
    if isinstance(llt, mutype.MuType):
        return llt
    if llt is llmemory.Address:
        return _lltype2mu_addr(llt)
    elif isinstance(llt, lltype.Primitive):
        return _lltype2mu_prim(llt)
    elif isinstance(llt, lltype.FixedSizeArray):
        return _lltype2mu_arrfix(llt)
    elif isinstance(llt, lltype.Struct):
        return _lltype2mu_stt(llt)
    elif isinstance(llt, lltype.Array):
        return _lltype2mu_arr(llt)
    elif isinstance(llt, lltype.Ptr):
        return _lltype2mu_ptr(llt)
    elif isinstance(llt, lltype.OpaqueType):
        log.warning("mapping type %r -> void" % llt)
        return mutype.void_t
    else:
        raise NotImplementedError("Don't know how to specialise %s using MuTS." % llt)
# ll2mu_ty = ll.saferecursive(_ll2mu_ty, None)


def _lltype2mu_prim(llt):
    type_map = {
        lltype.Signed:           mutype.int32_t,
        lltype.Unsigned:         mutype.int32_t,
        lltype.SignedLongLong:   mutype.int64_t,
        lltype.UnsignedLongLong: mutype.int64_t,
        # ll.SignedLongLongLong: MuInt(128),

        lltype.Float:            mutype.double_t,
        lltype.SingleFloat:      mutype.float_t,
        lltype.LongFloat:        mutype.double_t,

        lltype.Char:             mutype.int8_t,
        lltype.Bool:             mutype.int1_t,
        lltype.Void:             mutype.void_t,
        lltype.UniChar:          mutype.int16_t,
    }
    try:
        return type_map[llt]
    except KeyError:
        if llt._type in _inttypes.values():
            return mutype.MuInt(llt._type.BITS)
        raise NotImplementedError("Don't know how to specialise %s using MuTS." % llt)


def _lltype2mu_arrfix(llt):
    return mutype.MuArray(ll2mu_ty(llt.OF), llt.length)

_sttcache = {}


def _lltype2mu_stt(llt):
    if llt._is_varsize():
        return _lltype2mu_varstt(llt)
    try:
        return _sttcache[llt]
    except KeyError:
        stt = mutype.MuStruct(llt._name)
        _sttcache[llt] = stt
        lst = []
        for n, t in llt._flds.items():
            t_mu = ll2mu_ty(t)
            if not (t_mu is mutype.void_t or (isinstance(t_mu, mutype.MuRef) and t_mu.TO is mutype.void_t)):
                lst.append((n, t_mu))
        stt._setfields(lst)
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
    return mutype.MuHybrid(llt._name, *([(n, ll2mu_ty(flds[n])) for n in names[:-1]] + [(llt._arrayfld, var_t)]))


def _lltype2mu_arr(llt):
    return mutype.MuHybrid("%s" % llt.OF.__name__, ('length', mutype.int64_t), ('items', ll2mu_ty(llt.OF)))


def _lltype2mu_ptr(llt):
    if isinstance(llt.TO, lltype.FuncType):
        return _lltype2mu_funcptr(llt)
    return mutype.MuRef(ll2mu_ty(llt.TO))


def _lltype2mu_funcptr(llt):
    llfnc_t = llt.TO
    arg_ts = tuple([ll2mu_ty(arg) for arg in llfnc_t.ARGS if arg != lltype.Void])
    rtn_t = (ll2mu_ty(llfnc_t.RESULT), )
    sig = mutype.MuFuncSig(arg_ts, rtn_t)
    return mutype.MuFuncRef(sig)


def _lltype2mu_addr(llt):
    return mutype.MuUPtr(mutype.void_t)     # all Address types are translated into uptr<void>

# ----------------------------------------------------------
__ll2muval_cache = {}
__ll2muval_cache_ptr = {}


def ll2mu_val(llv):
    if isinstance(llv, mutype._muobject):
        return llv
    if isinstance(llv, CDefinedIntSymbolic):
        llv = llv.default
    elif isinstance(llv, TotalOrderSymbolic):
        llv = llv.compute_fn()
    elif isinstance(llv, ItemOffset):
        llv = mutype.mu_sizeOf(ll2mu_ty(llv.TYPE))

    cache, v = (__ll2muval_cache_ptr, llv._obj) if isinstance(llv, lltype._ptr) else (__ll2muval_cache, llv)
    try:
        return cache[v]
    except KeyError:
        muv = _ll2mu_val(llv)
        cache[v] = muv
        return muv


def _ll2mu_val(llv):
    """
    Map LLTS value types to MuTS value types
    :param llv: LLTS value
    :param llt: optional LLType, if the type information cannot be obtained from llv (Primitives)
    :return: _muobject
    """
    llt = lltype.typeOf(llv)
    if isinstance(llt, lltype.Primitive):
        return _llval2mu_prim(llv)

    elif isinstance(llv, lltype._fixedsizearray):
        return _llval2mu_arrfix(llv)

    elif isinstance(llv, lltype._struct):
        return _llval2mu_stt(llv)

    elif isinstance(llv, lltype._array):
        return _llval2mu_arr(llv)

    elif isinstance(llv, lltype._ptr):
        return _llval2mu_ptr(llv)
    else:
        raise NotImplementedError("Don't know how to specialise value %r of type %r." % (llv, lltype.typeOf(llv)))


def _llval2mu_prim(llv):
    mut = ll2mu_ty(lltype.typeOf(llv))
    if isinstance(llv, TotalOrderSymbolic):
        llv = llv.compute_fn()
    elif isinstance(llv, CDefinedIntSymbolic):
        llv = llv.default
    elif isinstance(llv, str):  # char
        llv = ord(llv)

    return mutype._muprimitive(mut, llv)


def _llval2mu_arrfix(llv):
    mut = ll2mu_ty(llv._TYPE)
    arr = mutype._muarray(mut)
    for i in range(llv.getlength()):
        arr[i] = ll2mu_val(llv.getitem(i))

    return arr


def _llval2mu_stt(llv):
    if llv._TYPE._arrayfld:
        return _llval2mu_varstt(llv)

    mut = ll2mu_ty(llv._TYPE)
    stt = mutype._mustruct(mut)
    for fld in mut._names:
        setattr(stt, fld, ll2mu_val(getattr(llv, fld)))

    return stt


def _llval2mu_varstt(llv):
    mut = ll2mu_ty(llv._TYPE)
    arr = getattr(llv, llv._TYPE._arrayfld)
    hyb = mutype._muhybrid(mut, mut.length(arr.getlength()))

    for fld in llv._TYPE._names[:-1]:
        setattr(hyb, fld, ll2mu_val(getattr(llv, fld)))

    for i in range(arr.getlength()):
        getattr(hyb, mut._varfld)[i] = ll2mu_val(arr.getitem(i))

    hyb.length = ll2mu_val(arr.getlength())

    return hyb


def _llval2mu_arr(llv):
    mut = ll2mu_ty(llv._TYPE)
    hyb = mutype._muhybrid(mut, ll2mu_val(llv.getlength()))

    for i in range(hyb.length.val):
        hyb[i] = ll2mu_val(llv.getitem(i))

    return hyb


def _llval2mu_ptr(llv):
    if llv._obj0 is None:
        return mutype._munullref(ll2mu_ty(llv._TYPE))
    if isinstance(llv._TYPE.TO, lltype.FuncType):
        return _llval2mu_funcptr(llv)
    mut = ll2mu_ty(llv._TYPE)
    return mutype._muref(mut, ll2mu_val(llv._obj))


def _llval2mu_funcptr(llv):
    mut = ll2mu_ty(llv._TYPE)
    return mutype._mufuncref(mut,
                          graph=getattr(llv._obj, 'graph', None),
                          fncname=getattr(llv._obj, '_name', ''),
                          compilation_info=getattr(llv._obj, 'compilation_info', None))


# ----------------------------------------------------------
def ll2mu_op(llop):
    return _ll2mu_op(llop.opname, llop.args, llop.result)


def _ll2mu_op(opname, args, result=None):
    try:
        return globals()['_llop2mu_' + opname](*args, res=result, llopname=opname)
    except KeyError:
        # try if it's an integer operation that can be redirected.
        contains = lambda s, subs: reduce(lambda a, b: a or b, map(lambda e: e in s, subs), False)
        if contains(opname, ('uint', 'char', 'long')):
            opname = "int_%s" % opname.split('_')[1]
            try:
                return globals()['_llop2mu_' + opname](*args, res=result, llopname=opname)
            except KeyError:
                pass    # raise error on next line
        raise NotImplementedError("Has not implemented specialisation for operation '%s'" % opname)


def _newprimconst(mut, primval):
    c = Constant(mut(primval))
    c.mu_type = mut
    c.mu_name = MuName(str(primval))
    return c


class _MuOpList(list):
    def append(self, op):
        list.append(self, op)
        return op.result

    def extend(self, oplist):
        if len(oplist) > 0:
            list.extend(self, oplist)
            return self[-1].result
        return None


# ----------------
# exception transform ops
def _llop2mu_mu_throw(exc, res=None, llopname='mu_throw'):
    return [muops.THROW(exc)]


# ----------------
# call ops
def _llop2mu_direct_call(cst_fnc, *args, **kwargs):
    g = cst_fnc.value.graph
    res = kwargs['res'] if 'res' in kwargs else None
    return [muops.CALL(g, args, result=res)]


def _llop2mu_indirect_call(var_callee, *args, **kwargs):
    res = kwargs['res'] if 'res' in kwargs else None
    return [muops.CALL(var_callee, args[:-1], result=res)]


# ----------------
# primitive ops
def _llop2mu_bool_not(x, res=None, llopname='bool_not'):
    return [muops.XOR(x, _newprimconst(x.mu_type, 1), result=res)]


def _llop2mu_int_is_true(x, res=None, llopname='int_is_true'):
    return [muops.NE(x, _newprimconst(x.mu_type, 0), result=res)]


def _llop2mu_int_neg(x, res=None, llopname='int_neg'):
    return [muops.SUB(_newprimconst(x.mu_type, 0), x, result=res)]


def _llop2mu_int_abs(x, res=None, llopname='int_abs'):
    ops = _MuOpList()
    # -x = 0 - x
    neg_x = ops.extend(_ll2mu_op('int_neg', [x]))
    # x > 0?
    cmp_res = ops.extend(_ll2mu_op('int_gt', [x, _newprimconst(x.mu_type, 0)]))
    # True -> x, False -> -x
    ops.append(muops.SELECT(cmp_res, x, neg_x, result=res))
    return ops


def _llop2mu_int_invert(x, res=None, llopname='int_invert'):
    # 2's complement
    # x' = (-x) - 1
    ops = _MuOpList()
    neg_x = ops.extend(_ll2mu_op('int_neg', [x]))
    one = _newprimconst(x.mut, 1)
    ops.extend(_ll2mu_op('_int_sub', (neg_x, one), res))
    return ops


def _llop2mu_int_between(a, x, b, res=None, llopname='int_between'):
    ops = _MuOpList()
    le_res = ops.extend(_ll2mu_op('int_le', (a, x)))
    lt_res = ops.extend(_ll2mu_op('int_lt',(x, b)))
    ops.extend(_ll2mu_op('int_and', (le_res, lt_res), res))
    return ops


def _llop2mu_int_force_ge_zero(x, res=None, llopname='int_force_ge_zero'):
    return _llop2mu_int_abs(x, res)


def _llop2mu_float_abs(x, res=None, llopname='float_abs'):
    ops = _MuOpList()
    # -x = 0 - x
    neg_x = ops.extend(_ll2mu_op('float_neg', [x]))
    f_0 = ops[-1].args[0]
    # x > 0 ?
    cmp_res = ops.extend(_ll2mu_op('float_gt', (x, f_0)))
    # True -> x, False -> (-x)
    ops.append(muops.SELECT(cmp_res, x, neg_x, result=res))
    return ops


__primop_map = {
    'int_floordiv':     'SDIV',
    'int_mod':          'SREM',
    'int_lshift':       'SHL',
    'int_rshift':       'ASHR',
    'uint_floordiv':    'UDIV',
    'uint_mod':         'UREM',
    'uint_lshift':      'SHL',
    'uint_rshift':      'LSHR',
    'float_add':        'FADD',
    'float_mul':        'FMUL',
    'float_truediv':    'FDIV',
    'int_eq':           'EQ',
    'int_ne':           'NE',
    'float_eq':         'FOEQ',
    'float_ne':         'FONE'
}

for op in "add sub mul and or xor".split(' '):
    __primop_map['int_' + op] = op.upper()
for cmp in 'lt le gt ge'.split(' '):
    __primop_map['int_' + cmp] = 'S' + cmp.upper()
    __primop_map['uint_' + cmp] = 'U' + cmp.upper()
    __primop_map['float_' + cmp] = 'FO' + cmp.upper()

for key in __primop_map:
    globals()['_llop2mu_' + key] = \
        lambda a, b, res, llopname: [getattr(muops, __primop_map[llopname])(a, b, result=res)]


# ----------------
# primitive cast ops
__cast_map = {
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

for pair in __cast_map:
    if isinstance(pair, tuple):
        name = 'cast_%s_to_%s' % pair
        __cast_map[name] = __cast_map[pair]
        del __cast_map[pair]
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


# ----------------
# pointer operations
def _llop2mu_malloc(T, res=None, llopname='malloc'):
    return [muops.NEW(T.value, result=res)]


def _llop2mu_malloc_varsize(T, n, res=None, llopname='malloc_varsize'):
    return [muops.NEWHYBRID(T.value, n, result=res)]


def __getfieldiref(var, fld):
    ops = _MuOpList()
    iref = var if isinstance(var.mu_type, (mutype.MuIRef, mutype.MuUPtr)) else ops.append(muops.GETIREF(var))
    mu_t = iref.mu_type.TO
    if isinstance(mu_t, mutype.MuHybrid) and fld == mu_t._varfld:
        iref_fld = ops.append(muops.GETVARPARTIREF(iref))
    else:
        idx = mu_t._index_of(fld)
        iref_fld = ops.append(muops.GETFIELDIREF(iref, idx))
    return iref_fld, ops


def _llop2mu_getfield(var, cnst_fldname, res=None, llopname='getfield'):
    iref_fld, ops = __getfieldiref(var, cnst_fldname.value)
    ops.append(muops.LOAD(iref_fld, result=res))
    return ops


def _llop2mu_setfield(var, cnst_fldname, val, res=None, llopname='setfield'):
    iref_fld, ops = __getfieldiref(var, cnst_fldname.value)
    ops.append(muops.STORE(iref_fld, val))
    return ops


def __getarrayitemiref(var, idx):
    iref_var, ops = __getfieldiref(var, var.mu_type.TO._varfld)
    iref_itm = ops.append(muops.SHIFTIREF(iref_var, idx))
    return iref_itm, ops


def _llop2mu_getarrayitem(var, idx, res=None, llopname='getarrayitem'):
    iref_itm, ops = __getarrayitemiref(var, idx)
    ops.append(muops.LOAD(iref_itm, result=res))
    return ops


def _llop2mu_setarrayitem(var, idx, val, res=None, llopname='setarrayitem'):
    iref_itm, ops = __getarrayitemiref(var, idx)
    ops.append(muops.STORE(iref_itm, val))
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
            iref = ops.append(muops.SHIFTIREF(iref, o))

    return iref, ops


def _llop2mu_getinteriorfield(var, *offsets, **kwargs):
    iref, ops = __getinterioriref(var, offsets)
    res = kwargs['res'] if 'res' in kwargs else None
    ops.append(muops.LOAD(iref, result=res))
    return ops


def _llop2mu_setinteriorfield(var, *offsets_val, **kwards):
    offsets, val = offsets_val[:-1], offsets_val[-1]
    iref, ops = __getinterioriref(var, offsets)
    ops.append(muops.STORE(iref, val))
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
    return [muops.REFCAST(var_ptr, res.mu_type if res else ll2mu_ty(cst_TYPE.value), result=res)]


def _llop2mu_ptr_eq(ptr1, ptr2, res=None, llopname='ptr_eq'):
    return [muops.EQ(ptr1, ptr2, result=res)]


def _llop2mu_ptr_ne(ptr1, ptr2, res=None, llopname='ptr_eq'):
    return [muops.NE(ptr1, ptr2, result=res)]


def _llop2mu_ptr_nonzero(ptr, res=None, llopname='ptr_nonzero'):
    cst = Constant(mutype._munullref(ptr.mu_type))
    cst.mu_type = ptr.mu_type
    cst.mu_name = MuName("NULL_%s" % ptr.mu_type.mu_name._name)
    return _llop2mu_ptr_ne(ptr, cst, res)


def _llop2mu_ptr_zero(ptr, res=None, llopname='ptr_zero'):
    cst = Constant(mutype._munullref(ptr.mu_type))
    cst.mu_type = ptr.mu_type
    cst.mu_name = MuName("NULL_%s" % ptr.mu_type.mu_name._name)
    return _llop2mu_ptr_eq(ptr, cst, res)


# ----------------
# address operations
def _llop2mu_keepalive(ptr, res=None, llopname='keepalive'):
    return [muops.NATIVE_UNPIN(ptr, result=res)]


def __raw2ccall(*args, **kwargs):
    ops = _MuOpList()
    externfnc = getattr(muni, kwargs['llopname'].replace('raw', 'c'))
    fnp = ops.append(muops.LOAD(externfnc))
    ops.append(muops.CCALL(fnp, args, result=kwargs['res']))
    return ops

for op in 'malloc free memset memcopy memmove'.split(' '):
    globals()['_llop2mu_raw_' + op] = __raw2ccall


# def _llop2mu_raw_memclear():
#     pass
#
#
# def _llop2mu_raw_load():
#     pass
#
#
# def _llop2mu_raw_store():
#     pass


def _llop2mu_adr_add(ptr, ptr2, res=None, llopname='adr_add'):
    def _proc_offset(ptr, o):
        ptr.mu_type = mutype.MuUPtr(ll2mu_ty(o.TYPE))
        if isinstance(o, llmemory.FieldOffset):
            ptr, _ops = __getfieldiref(ptr, o.fldname)
            ops.extend(_ops)
        if isinstance(o, llmemory.ArrayItemsOffset):
            pass  # assuming the uptr is already at the start of the memarray.
        if isinstance(o, llmemory.ItemOffset):
            ptr = ops.append(muops.SHIFTIREF(ptr,
                                             _newprimconst(mutype.int64_t,
                                                           o.repeat if llopname == 'adr_add' else -o.repeat)))
        return ptr
    ops = _MuOpList()
    if isinstance(ptr2, Constant):
        if isinstance(ptr2.value, llmemory.CompositeOffset):
            for o in ptr2.value.offsets:
                ptr = _proc_offset(ptr, o)
        elif isinstance(ptr2.value, llmemory.AddressOffset):
            ptr = _proc_offset(ptr, ptr2.value)
        elif isinstance(ptr2.concretetype, lltype.Primitive):
            adr_src = ops.extend(__cast_ptr_to_int(ptr))
            adr_res = ops.extend(_ll2mu_op('int_add', (adr_src, ptr2)))
            ops.extend(_ll2mu_op('cast_int_to_adr', (adr_res,), res))

        if len(ops) > 0:
            ops[-1].result = res
    else:
        adr1 = ops.extend(__cast_ptr_to_int(ptr))
        adr2 = ops.extend(__cast_ptr_to_int(ptr2))
        adr = ops.extend(_ll2mu_op('int_add', (adr1, adr2)))
        ops.extend(_ll2mu_op('cast_int_to_adr', (adr, ), res))
    return ops


def _llop2mu_adr_sub(ptr, cnst_offsets, res=None, llopname='adr_sub'):
    return _llop2mu_adr_add(ptr, cnst_offsets, res, llopname)


def __cast_ptr_to_int(ptr, res=None):
    return [muops.PTRCAST(ptr, muni.__ptr_int_t, result=res)]


def _llop2mu_adr_delta(ptr1, ptr2, res=None, llopname='adr_delta'):
    ops = _MuOpList()
    adr1 = ops.extend(__cast_ptr_to_int(ptr1))
    adr2 = ops.extend(__cast_ptr_to_int(ptr2))
    ops.extend(_ll2mu_op('int_sub', (adr2, adr1), res))
    return ops


def __adr_cmp(ptr1, ptr2, res=None, llopname=''):
    ops = _MuOpList()
    adr1 = ops.extend(__cast_ptr_to_int(ptr1))
    adr2 = ops.extend(__cast_ptr_to_int(ptr2))
    ops.extend(_ll2mu_op(llopname.replace('adr', 'int'), (adr1, adr2), res))
    return ops

for cmpop in "lt le eq ne gt ge".split(' '):
    globals()['_llop2mu_adr_' + cmpop] = __adr_cmp


def _llop2mu_cast_ptr_to_adr(ptr, res=None, llopname='cast_ptr_to_adr'):
    return [muops.NATIVE_PIN(ptr, result=res)]


def _llop2mu_cast_adr_to_int(ptr, res=None, llopname='cast_adr_to_int'):
    return __cast_ptr_to_int(ptr, res)


def _llop2mu_cast_int_to_adr(n, res=None, llopname='cast_adr_to_int'):
    return [muops.PTRCAST(n, ll2mu_ty(llmemory.Address), result=res)]


# TODO: rest of the operations
