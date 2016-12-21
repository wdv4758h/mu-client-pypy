from rpython.rtyper.lltypesystem import lltype, rffi
from rpython.translator.interactive import Translation
from rpython.translator.mu import mutype
from rpython.translator.mu.database import MuDatabase, MuNameManager
from rpython.translator.mu.genmu import MuBundleGen, hybrid2struct


def test_factorial(tmpdir):
    def factorial(n):
        if n <= 1:
            return 1
        return n * factorial(n - 1)

    t = Translation(factorial, [lltype.Unsigned], backend='mu')
    t.compile_mu()


def test_quicksort(tmpdir):
    def swap(arr, i, j):
        t = arr[i]
        arr[i] = arr[j]
        arr[j] = t

    def partition(arr, idx_low, idx_high):
        pivot = arr[idx_high]
        i = idx_low
        for j in range(idx_low, idx_high):
            if arr[j] < pivot:
                swap(arr, i, j)
                i += 1
        swap(arr, i, idx_high)
        return i

    def quicksort(arr, start, end):
        if start < end:
            p = partition(arr, start, end)
            quicksort(arr, start, p - 1)
            quicksort(arr, p + 1, end)

    t = Translation(quicksort, [rffi.CArrayPtr(rffi.LONGLONG), lltype.Signed, lltype.Signed], backend='mu')
    t.compile_mu()


def test_bigintbenchmark(tmpdir):
    from rpython.translator.goal.targetbigintbenchmark import entry_point
    t = Translation(entry_point, [str], backend='mu')
    t.compile_mu()


def test_identityhash():
    from rpython.rlib import objectmodel
    def f(x):
        return objectmodel.compute_identity_hash(x)

    t = Translation(f, [lltype.Ptr(lltype.GcStruct('stt', ('x', lltype.Signed)))], backend='mu')
    t.mutype()
    graphs = t.context.graphs
    assert len(graphs) == 2


def test_ovf():
    from rpython.rlib.rarithmetic import ovfcheck
    from rpython.translator.mu.test.test_mutyper import graph_of
    def f(a, b):
        try:
            return ovfcheck(a + b)
        except OverflowError:
            raise MemoryError

    t = Translation(f, [int, int], backend='mu')
    t.compile_mu()
    graph_f = graph_of(f, t)
    graph_f.view()


def test_init_heap():
    class A:
        def __init__(self, s):
            self.s = s

        def __str__(self):
            return self.s + '_suffix'

    a = A("string")

    def f():
        return str(a)

    t = Translation(f, [], backend='mu')
    t.compile_mu()


def test_hybrid2struct():
    from rpython.translator.mu.ll2mu import LL2MuMapper
    from rpython.rtyper.lltypesystem.rstr import STR

    Hyb = LL2MuMapper().map_type(STR)
    hyb = mutype.newhybrid(Hyb, 5)._obj
    h = mutype.mu_int64(hash(hyb))
    hyb.gc_idhash = h
    hyb.hash = h
    hyb.length = mutype.mu_int64(5)
    for i, c in enumerate("hello"):
        hyb.chars[i] = mutype.mu_int8(ord(c))

    stt = hybrid2struct(hyb)
    assert isinstance(mutype.mutypeOf(stt), mutype.MuStruct)
    assert stt.gc_idhash == h
    assert stt.hash == h
    assert stt.length == mutype.mu_int64(5)
    for i, c in enumerate("hello"):
        assert stt.chars[i] == mutype.mu_int8(ord(c))
