from rpython.rtyper.lltypesystem import lltype as ll
from .muts import mutype as mu
from rpython.rtyper.normalizecalls import TotalOrderSymbolic
from rpython.rlib.objectmodel import CDefinedIntSymbolic

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
    if isinstance(llt, ll.Primitive):
        return _lltype_prim2mu(llt)
    elif isinstance(llt, ll.FixedSizeArray):
        return _lltype_arrfix2mu(llt)
    elif isinstance(llt, ll.Struct):
        return _lltype_stt2mu(llt)
    elif isinstance(llt, ll.Array):
        return _lltype_arr2mu(llt)
    elif isinstance(llt, ll.Ptr):
        return _lltype_ptr2mu(llt)
    elif isinstance(llt, ll.OpaqueType):
        log.warning("mapping type %r -> void" % llt)
        return mu.void_t
    else:
        raise NotImplementedError("Don't know how to specialise %s using MuTS." % llt)
# ll2mu_ty = ll.saferecursive(_ll2mu_ty, None)


def _lltype_prim2mu(llt):
    type_map = {
        ll.Signed:             mu.int32_t,
        ll.Unsigned:           mu.int32_t,
        ll.SignedLongLong:     mu.int64_t,
        ll.UnsignedLongLong:   mu.int64_t,
        # ll.SignedLongLongLong: MuInt(128),

        ll.Float:              mu.double_t,
        ll.SingleFloat:        mu.float_t,
        ll.LongFloat:          mu.double_t,

        ll.Char:               mu.int8_t,
        ll.Bool:               mu.int1_t,
        ll.Void:               mu.void_t,
        ll.UniChar:            mu.int16_t,
    }
    try:
        return type_map[llt]
    except KeyError:
        raise NotImplementedError("Don't know how to specialise %s using MuTS." % llt)


def _lltype_arrfix2mu(llt):
    return mu.MuArray(ll2mu_ty(llt.OF), llt.length)

_sttcache = {}


def _lltype_stt2mu(llt):
    if llt._is_varsize():
        return _lltype_varstt2mu(llt)
    try:
        return _sttcache[llt]
    except KeyError:
        stt = mu.MuStruct(llt._name)
        _sttcache[llt] = stt
        stt._setfields([(n, ll2mu_ty(llt._flds[n])) for n in llt._names])
        return stt


def _lltype_varstt2mu(llt):
    var_t = ll2mu_ty(llt._flds[llt._arrayfld].OF)
    if 'length' not in llt._names:
        names = list(llt._names)
        names.insert(-1, 'length')
        flds = llt._flds.copy()
        flds['length'] = ll.Signed
    else:
        names = llt._names
        flds = llt._flds
    return mu.MuHybrid(llt._name, *([(n, ll2mu_ty(flds[n])) for n in names[:-1]] + [(llt._arrayfld, var_t)]))


def _lltype_arr2mu(llt):
    return mu.MuHybrid("%s" % llt.OF._name, ('length', mu.int64_t), ('items', ll2mu_ty(llt.OF)))


def _lltype_ptr2mu(llt):
    if isinstance(llt.TO, ll.FuncType):
        return _lltype_funcptr2mu(llt)
    return mu.MuRef(ll2mu_ty(llt.TO))


def _lltype_funcptr2mu(llt):
    llfnc_t = llt.TO
    arg_ts = tuple([ll2mu_ty(arg) for arg in llfnc_t.ARGS if arg != ll.Void])
    rtn_t = (ll2mu_ty(llfnc_t.RESULT), )
    sig = mu.MuFuncSig(rtn_t, arg_ts)
    return mu.MuFuncRef(sig)


# ----------------------------------------------------------
def ll2mu_val(llv, llt=None):
    """
    Map LLTS value types to MuTS value types
    :param llv: LLTS value
    :param llt: optional LLType, if the type information cannot be obtained from llv (Primitives)
    :return: _muobject
    """
    if isinstance(llv, (int, float)):
        if not isinstance(llt, ll.Primitive):
            raise TypeError("Wrong type information '%r' for specialising %r" % (llt, llv))
        return _llval_prim2mu(llv, llt)

    elif isinstance(llv, ll._fixedsizearray):
        return _llval_arrfix2mu(llv)

    elif isinstance(llv, ll._struct):
        return _llval_stt2mu(llv)

    elif isinstance(llv, ll._array):
        return _llval_arr2mu(llv)

    elif isinstance(llv, ll._ptr):
        return _llval_ptr2mu(llv)
    elif llt == ll.Char and len(llv) == 1:
        return _llval_prim2mu(ord(llv), llt)
    else:
        raise NotImplementedError("Don't know how to specialise value type %r." % llv)


def _llval_prim2mu(llv, llt):
    mut = ll2mu_ty(llt)
    if isinstance(llv, TotalOrderSymbolic):
        llv = llv.compute_fn()
    elif isinstance(llv, CDefinedIntSymbolic):
        llv = llv.default

    return mu._muprimitive(mut, llv)


def _llval_arrfix2mu(llv):
    mut = ll2mu_ty(llv._TYPE)
    arr = mu._muarray(mut)
    for i in range(llv.getlength()):
        arr[i] = ll2mu_val(llv.getitem(i), llv._TYPE.OF)

    return arr


def _llval_stt2mu(llv):
    if llv._TYPE._arrayfld:
        return _llval_varstt2mu(llv)

    mut = ll2mu_ty(llv._TYPE)
    stt = mu._mustruct(mut)
    for fld in llv._TYPE._names:
        setattr(stt, fld, ll2mu_val(getattr(llv, fld), getattr(llv._TYPE, fld)))

    return stt


def _llval_varstt2mu(llv):
    mut = ll2mu_ty(llv._TYPE)
    arr = getattr(llv, llv._TYPE._arrayfld)
    hyb = mu._muhybrid(mut, arr.getlength())

    for fld in llv._TYPE._names[:-1]:
        setattr(hyb, fld, ll2mu_val(getattr(llv, fld), getattr(llv._TYPE, fld)))

    for i in range(arr.getlength()):
        getattr(hyb, mut._varfld)[i] = ll2mu_val(arr.getitem(i), arr._TYPE.OF)

    hyb.length = ll2mu_val(arr.getlength(), ll.Signed)

    return hyb


def _llval_arr2mu(llv):
    mut = ll2mu_ty(llv._TYPE)
    hyb = mu._muhybrid(mut, llv.getlength())

    hyb.length = ll2mu_val(llv.getlength(), mut.length)    # Hybrids converted from Array should have a 'length' field
    for i in range(hyb.length):
        hyb[i] = ll2mu_val(llv.getitem(i), llv._TYPE.OF)

    return hyb


def _llval_ptr2mu(llv):
    mut = ll2mu_ty(llv._TYPE)
    return mu._muref(mut, ll2mu_val(llv._obj))