from rpython.rtyper.lltypesystem import lltype as ll
from .muts import mutype as mu
import py
from rpython.tool.ansi_print import ansi_log


log = py.log.Producer("ll2mu")
py.log.setconsumer("ll2mu", ansi_log)


# ----------------------------------------------------------
def ll2mu_ty(llt):
    if isinstance(llt, ll.Primitive):
        return _llprim2mu(llt)
    elif isinstance(llt, ll.FixedSizeArray):
        return _llarrfix2mu(llt)
    elif isinstance(llt, ll.Struct):
        return _llstt2mu(llt)
    elif isinstance(llt, ll.Array):
        return _llarr2mu(llt)
    elif isinstance(llt, ll.Ptr):
        return _llptr2mu(llt)
    elif isinstance(llt, ll.OpaqueType):
        log.warning("mapping type %r -> void" % llt)
        return mu.void_t
    else:
        raise NotImplementedError("Don't know how to specialise %s using MuTS." % llt)
# ll2mu_ty = ll.saferecursive(_ll2mu_ty, None)


def _llprim2mu(llt):
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


def _llarrfix2mu(llt):
    return mu.MuArray(ll2mu_ty(llt.OF), llt.length)

_sttcache = {}


def _llstt2mu(llt):
    if llt._is_varsize():
        return _llvarstt2mu(llt)
    try:
        return _sttcache[llt]
    except KeyError:
        stt = mu.MuStruct(llt._name)
        _sttcache[llt] = stt
        stt._setfields(*[(n, ll2mu_ty(llt._flds[n])) for n in llt._names])
        return stt


def _llvarstt2mu(llt):
    var_t = ll2mu_ty(llt._flds[llt._arrayfld].OF)
    return mu.MuHybrid(llt._name, *([(n, ll2mu_ty(llt._flds[n])) for n in llt._names[:-1]] + [(llt._arrayfld, var_t)]))


def _llarr2mu(llt):
    return mu.MuHybrid("%s" % llt.OF._name, ('length', mu.int64_t), ('items', ll2mu_ty(llt.OF)))


def _llptr2mu(llt):
    if isinstance(llt.TO, ll.FuncType):
        return _llfuncptr2mu(llt)
    return mu.MuRef(ll2mu_ty(llt.TO))


def _llfuncptr2mu(llt):
    llfnc_t = llt.TO
    arg_ts = tuple([ll2mu_ty(arg) for arg in llfnc_t.ARGS if arg != ll.Void])
    rtn_t = (ll2mu_ty(llfnc_t.RESULT), )
    sig = mu.MuFuncSig(rtn_t, arg_ts)
    return mu.MuFuncRef(sig)


# ----------------------------------------------------------
