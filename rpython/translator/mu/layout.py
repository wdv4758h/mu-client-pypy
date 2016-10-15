"""
Mu object memory layout
"""
from rpython.translator.mu.mutype import *


def _alignUp(n, sz):
    return n if n % sz == 0 else (n / sz + 1) * sz


__prim_map = {
    MU_INT1: 1,
    MU_INT8: 1,
    MU_INT16: 2,
    MU_INT32: 4,
    MU_INT64: 8,
    MU_FLOAT: 4,
    MU_DOUBLE: 8
}


def mu_sizeOf(mutype):
    if isinstance(mutype, MuHybrid):
        raise TypeError("Cannot get size of MuHybrid type.")

    if not isinstance(mutype, MuContainerType):
        return mu_alignOf(mutype)

    if isinstance(mutype, MuStruct):
        return _alignUp(reduce(lambda n, ty: _alignUp(n, mu_alignOf(ty)) + mu_sizeOf(ty),
                              map(lambda fld: getattr(mutype, fld), mutype._names),
                              0),
                       mu_alignOf(mutype))

    if isinstance(mutype, MuArray):
        return _alignUp(mu_sizeOf(mutype.OF), mu_alignOf(mutype.OF)) * mutype.length


def mu_hybsizeOf(hyb_t, n):
    """
    Return the size of a MuHybrid type with n allocated items.
    """
    fixstt = MuStruct('fix', *[(f, getattr(hyb_t, f)) for f in hyb_t._names[:-1]])
    fix_sz = mu_sizeOf(fixstt)
    var_t = getattr(hyb_t, hyb_t._varfld)
    var_align = mu_alignOf(var_t)
    var_sz = mu_offsetOf(MuArray(var_t, n), n)
    return _alignUp(fix_sz, var_align) + var_sz


def mu_alignOf(mutype):

    try:
        return __prim_map[mutype]
    except KeyError:
        pass

    if isinstance(mutype, MuReferenceType):
        return 8

    if isinstance(mutype, MuStruct):
        if len(mutype._names) == 0:
            return 1
        # elif len(mutype._names) == 1:
        #     return mu_alignOf(getattr(mutype, mutype._names[0]))
        else:
            return max(mu_alignOf(getattr(mutype, fld)) for fld in mutype._names)

    if isinstance(mutype, MuArray):
        return mu_alignOf(mutype.OF)


def mu_offsetOf(mutype, fld):
    if isinstance(mutype, MuStruct):
        idx = mutype._index_of(fld)
        fldalign = mu_alignOf(getattr(mutype, fld))
        prestt = MuStruct('tmp', *[(fld, getattr(mutype, fld)) for fld in mutype._names[:idx]])
        prefixsizeof = mu_sizeOf(prestt)
        return _alignUp(prefixsizeof, fldalign)

    if isinstance(mutype, MuArray):
        of = mutype.OF
        return _alignUp(mu_sizeOf(of), mu_alignOf(of)) * fld

    if isinstance(mutype, MuHybrid):
        fixstt = MuStruct('fix', *[(f, getattr(mutype, f)) for f in mutype._names[:-1]])
        if fld == mutype._varfld:
            return _alignUp(mu_sizeOf(fixstt), mu_alignOf(getattr(mutype, fld)))
        else:
            return mu_offsetOf(fixstt, fld)
