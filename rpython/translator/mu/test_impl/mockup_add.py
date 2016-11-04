from rpython.rtyper.lltypesystem import rffi
from rpython.translator.interactive import Translation


def find_min(xs, sz):
    m = xs[0]
    for i in range(1, sz):
        x = xs[i]
        if x < m:
            m = x
    return m


def add(a, b):
    return a + b


if __name__ == '__main__':
    import ctypes
    # t = Translation(find_min, [rffi.CArrayPtr(rffi.ULONGLONG), rffi.INT],
    #                 backend='mu', muimpl='fast', mucodegen='api', mutestjit=True)
    t = Translation(add, [rffi.ULONGLONG, rffi.ULONGLONG],
                    backend='mu', muimpl='fast', mucodegen='api', mutestjit=True)
    db, bdlgen, fnc_name = t.compile_mu()
    bdlgen.mu.compile_to_sharedlib('libtesting.dylib', [])
    lib = ctypes.CDLL('emit/libtesting.dylib')
    fnc = getattr(lib, fnc_name)
    assert fnc(1, 2) == 3
