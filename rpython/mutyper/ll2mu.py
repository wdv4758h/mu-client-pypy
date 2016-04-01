from rpython.rtyper.lltypesystem import lltype
from .muts import mutype
from .muts import muops
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
    if isinstance(llt, lltype.Primitive):
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
        stt._setfields([(n, ll2mu_ty(llt._flds[n])) for n in llt._names])
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
    return mutype.MuHybrid("%s" % llt.OF._name, ('length', mutype.int64_t), ('items', ll2mu_ty(llt.OF)))


def _lltype2mu_ptr(llt):
    if isinstance(llt.TO, lltype.FuncType):
        return _lltype2mu_funcptr(llt)
    return mutype.MuRef(ll2mu_ty(llt.TO))


def _lltype2mu_funcptr(llt):
    llfnc_t = llt.TO
    arg_ts = tuple([ll2mu_ty(arg) for arg in llfnc_t.ARGS if arg != lltype.Void])
    rtn_t = (ll2mu_ty(llfnc_t.RESULT), )
    sig = mutype.MuFuncSig(rtn_t, arg_ts)
    return mutype.MuFuncRef(sig)


# ----------------------------------------------------------
def ll2mu_val(llv, llt=None):
    """
    Map LLTS value types to MuTS value types
    :param llv: LLTS value
    :param llt: optional LLType, if the type information cannot be obtained from llv (Primitives)
    :return: _muobject
    """
    if isinstance(llv, (int, float)):
        if not isinstance(llt, lltype.Primitive):
            raise TypeError("Wrong type information '%r' for specialising %r" % (llt, llv))
        return _llval2mu_prim(llv, llt)

    elif isinstance(llv, lltype._fixedsizearray):
        return _llval2mu_arrfix(llv)

    elif isinstance(llv, lltype._struct):
        return _llval2mu_stt(llv)

    elif isinstance(llv, lltype._array):
        return _llval2mu_arr(llv)

    elif isinstance(llv, lltype._ptr):
        return _llval2mu_ptr(llv)
    elif llt == lltype.Char and len(llv) == 1:
        return _llval2mu_prim(ord(llv), llt)
    else:
        raise NotImplementedError("Don't know how to specialise value type %r." % llv)


def _llval2mu_prim(llv, llt):
    mut = ll2mu_ty(llt)
    if isinstance(llv, TotalOrderSymbolic):
        llv = llv.compute_fn()
    elif isinstance(llv, CDefinedIntSymbolic):
        llv = llv.default

    return mutype._muprimitive(mut, llv)


def _llval2mu_arrfix(llv):
    mut = ll2mu_ty(llv._TYPE)
    arr = mutype._muarray(mut)
    for i in range(llv.getlength()):
        arr[i] = ll2mu_val(llv.getitem(i), llv._TYPE.OF)

    return arr


def _llval2mu_stt(llv):
    if llv._TYPE._arrayfld:
        return _llval2mu_varstt(llv)

    mut = ll2mu_ty(llv._TYPE)
    stt = mutype._mustruct(mut)
    for fld in llv._TYPE._names:
        setattr(stt, fld, ll2mu_val(getattr(llv, fld), getattr(llv._TYPE, fld)))

    return stt


def _llval2mu_varstt(llv):
    mut = ll2mu_ty(llv._TYPE)
    arr = getattr(llv, llv._TYPE._arrayfld)
    hyb = mutype._muhybrid(mut, mut.length(arr.getlength()))

    for fld in llv._TYPE._names[:-1]:
        setattr(hyb, fld, ll2mu_val(getattr(llv, fld), getattr(llv._TYPE, fld)))

    for i in range(arr.getlength()):
        getattr(hyb, mut._varfld)[i] = ll2mu_val(arr.getitem(i), arr._TYPE.OF)

    hyb.length = ll2mu_val(arr.getlength(), lltype.Signed)

    return hyb


def _llval2mu_arr(llv):
    mut = ll2mu_ty(llv._TYPE)
    hyb = mutype._muhybrid(mut, llv.getlength())

    hyb.length = ll2mu_val(llv.getlength(), mut.length)    # Hybrids converted from Array should have a 'length' field
    for i in range(hyb.length):
        hyb[i] = ll2mu_val(llv.getitem(i), llv._TYPE.OF)

    return hyb


def _llval2mu_ptr(llv):
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
# primitive ops
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
def _llop2mu_malloc(T, flavor, res=None, llopname='malloc'):
    return [muops.NEW(T.value, result=res)]


def _llop2mu_malloc_varsize(T, n, flavor, res=None, llopname='malloc_varsize'):
    return [muops.NEWHYBRID(T.value, n, result=res)]


def __getfieldiref(var, fld):
    ops = _MuOpList()
    iref = var if isinstance(var.mu_type, mutype.MuIRef) else ops.append(muops.GETIREF(var))
    mu_t = iref.mu_type.TO
    if isinstance(mu_t, mutype.MuHybrid) and fld == mu_t._varfld:
        iref_fld = ops.append(muops.GETVARPARTIREF(iref))
    else:
        idx = mu_t._index_of(fld)
        iref_fld = ops.append(muops.GETFIELDIREF(iref, idx))
    return iref_fld, ops


def _llop2mu_getfield(var, cnst_fldname, res=None, llopname='getfield'):
    iref_fld, ops = __getfieldiref(var, cnst_fldname)
    ops.append(muops.LOAD(iref_fld, result=res))
    return ops


def _llop2mu_setfield(var, cnst_fldname, val, res=None, llopname='setfield'):
    iref_fld, ops = __getfieldiref(var, cnst_fldname)
    ops.append(muops.STORE(iref_fld, val, res))
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
    iref = var if isinstance(var.mu_type, mutype.MuIRef) else ops.append(muops.GETIREF(var))
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
    ops.extend(muops.STORE(iref, val))
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
    return [muops.REFCAST(var_ptr, res.mu_typem if res else ll2mu_ty(cst_TYPE.value), result=res)]


def _llop2mu_ptr_eq(ptr1, ptr2, res=None, llopname='ptr_eq'):
    return [muops.EQ(ptr1, ptr2, result=res)]


def _llop2mu_ptr_ne(ptr1, ptr2, res=None, llopname='ptr_eq'):
    return [muops.NE(ptr1, ptr2, result=res)]


def _llop2mu_ptr_nonzero(ptr, res=None, llopname='ptr_nonzero'):
    cst = Constant(mutype.NULL)
    cst.mu_type = ptr.mu_type
    return _llop2mu_ptr_ne(ptr, cst, res)


def _llop2mu_ptr_zero(ptr, res=None, llopname='ptr_zero'):
    cst = Constant(mutype.NULL)
    cst.mu_type = ptr.mu_type
    return _llop2mu_ptr_eq(ptr, cst, res)
