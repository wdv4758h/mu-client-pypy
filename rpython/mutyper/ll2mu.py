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
    try:
        return globals()['_llop2mu_' + llop.opname](*llop.args, res=llop.result, llopname=llop.opname)
    except KeyError:
        # try if it's an integer operation that can be redirected.
        contains = lambda s, subs: reduce(lambda a, b: a or b, map(lambda e: e in s, subs), False)
        if contains(llop.opname, ('uint', 'char', 'long')):
            opname = "int_%s" % llop.opname.split('_')[1]
            try:
                return globals()['_llop2mu_' + opname](*llop.args, res=llop.result, llopname=llop.opname)
            except KeyError:
                pass    # raise error on next line
        raise NotImplementedError("Has not implemented specialisation for operation '%s'" % llop.opname)


def _newprimconst(mut, primval):
    c = Constant(mut(primval))
    c.mu_type = mut
    return c


# ----------------
# primitive ops
def _llop2mu_int_is_true(x, res=None, llopname=None):
    return [muops.NE(x, _newprimconst(x.mu_type, 0), result=res)]


def _llop2mu_int_neg(x, res=None, llopname=None):
    return [muops.SUB(_newprimconst(x.mu_type, 0), x, result=res)]


def _llop2mu_int_abs(x, res=None, llopname=None):
    ops = []

    # -x = 0 - x
    ops += _llop2mu_int_neg(x)
    neg_x = ops[-1].result

    # x > 0?
    ops += globals()['_llop2mu_int_gt'](x, _newprimconst(x.mu_type, 0))
    cmp_res = ops[-1].result

    # True -> x, False -> -x
    ops.append(muops.SELECT(cmp_res, x, neg_x, result=res))

    return ops


def _llop2mu_int_invert(x, res=None, llopname=None):
    # 2's complement
    # x' = (-x) - 1
    ops = []

    ops += _llop2mu_int_neg(x)
    neg_x = ops[-1].result

    one = _newprimconst(x.mut, 1)

    ops += globals()['_llop2mu_int_sub'](neg_x, one, res)
    return ops


def _llop2mu_int_between(a, x, b, res=None, llopname=None):
    ops = []

    ops += globals()['_llop2mu_int_le'](a, x)
    le_res = ops[-1].result

    ops += globals()['_llop2mu_int_lt'](x, b)
    lt_res = ops[-1].result

    ops += globals()['_llop2mu_int_and'](le_res, lt_res, res)
    return ops


def _llop2mu_int_force_ge_zero(x, res=None, llopname=None):
    return _llop2mu_int_abs(x, res)


def _llop2mu_float_abs(x, res=None, llopname=None):
    ops = []

    # -x = 0 - x
    ops += globals()['_llop2mu_float_neg'](x)
    neg_x = ops[-1].result
    f_0 = ops[-1].args[0]

    # x > 0 ?
    ops += globals()['_llop2mu_float_gt'](x, f_0)
    cmp_res = ops[-1].result

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
def _llop2mu_malloc(T, res=None, llopname=None):
    return [muops.NEW(T.value, result=res)]


def _llop2mu_malloc_varsize(T, n, res=None, llopname=None):
    return [muops.NEWHYBRID(T.value, n, result=res)]
