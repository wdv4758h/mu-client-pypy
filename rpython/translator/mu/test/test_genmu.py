from rpython.rtyper.lltypesystem import lltype, rffi
from rpython.translator.interactive import Translation
from rpython.translator.mu.genmu import MuBundleGen


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
