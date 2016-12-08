from rpython.flowspace.model import Constant
from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.translator.interactive import Translation
from rpython.rlib import rposix
from rpython.translator.mu import mutype
from rpython.translator.mu.database import MuDatabase


def test_collect_global_defs():
    lst = [1, 5, -23]
    def f(idx):
        return lst[idx]

    t = Translation(f, [int], backend='mu')
    t.mutype()

    db = MuDatabase(t.context)
    db.collect_global_defs()

    # a MU_INT8 constant 1 might be eliminated by backend optimisations
    # 1, 5, -23 will be initialised in heap
    assert {Constant(mutype.mu_int64(0), mutype.MU_INT64),
            Constant(mutype.mu_int64(3), mutype.MU_INT64)}.issubset(db.consts)

    assert len(db.types) == 9   # void, i1, i8, i64, ref<i64>, hyb, ref<hyb>, iref<hyb>, (i64) -> (i64)
    assert len(db.gcells) == 1
