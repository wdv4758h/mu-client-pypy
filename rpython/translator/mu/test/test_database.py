from rpython.flowspace.model import Constant
from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.translator.interactive import Translation
from rpython.rlib import rposix
from rpython.translator.mu import mutype
from rpython.translator.mu.database import MuDatabase, MuNameManager

from rpython.translator.mu.test.test_mutyper import graph_of


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
    assert len(db.objtracer.heap_objs) == 1


def test_object_tracer():
    class Node:
        def __init__(self, x, prev=None):
            self.x = x
            if prev:
                self.nxt = prev.nxt
                prev.nxt = self
            else:
                self.nxt = None

    a = Node('a')
    b = Node('b', a)
    c = Node('c', b)

    def f(idx):
        nd = a
        while idx > 0:
            nd = nd.nxt
        return nd

    t = Translation(f, [int], backend='mu')
    t.mutype()

    db = MuDatabase(t.context)
    db.collect_global_defs()

    assert len(db.objtracer.heap_objs) == 4

    # @ MuStruct rpython.translator.mu.test.test_database.Node { super, inst_nxt, inst_x }
    # MuStruct rpython.translator.mu.test.test_database.Node { super, inst_nxt, inst_x }
    # * MuStruct object_vtable { subclassrange_min, subclassrange_max, rtti, name, hash, instantiate }
    # MuStruct object_vtable { subclassrange_min, subclassrange_max, rtti, name, hash, instantiate }
    # MuStruct rpython.translator.mu.test.test_database.Node_vtable { super }
    # MU_INT64
    # * MU_INT8
    # MU_INT8
    # @ MuHybrid rpy_string { gc_idhash, hash, length, chars }
    # MuHybrid rpy_string { gc_idhash, hash, length, chars }
    # FncRef(  ) -> ( @ MuStruct object { gc_idhash, typeptr } )
    # MuStruct object { gc_idhash, typeptr }
    assert len(db.objtracer.types_in_heap()) == 12

    assert len(db.objtracer.fixed_objs) == 2    # object_vtable, rtti (MU_INT8)


def exported_symbol_in_dylib(sym_name, libpath):
    # use nm program to get a list of symbols in shared library,
    # then check if the symbol name is in the list with 'T' (exported symbol)
    import subprocess
    from rpython.translator.platform import platform
    output = str(subprocess.check_output('nm %(flag)s %(libpath)s' % {
        'flag': '-D' if platform.name.startswith('linux') else '',
        'libpath': libpath
    }, shell=True))
    return 'T _%(sym_name)s' % locals() in output  # exported symbol


def test_extern_funcs_macro_wrapper():
    t = Translation(rposix.makedev, [int, int], backend='mu')
    t.rtype()
    t.mutype()

    db = MuDatabase(t.context)
    db.collect_global_defs()
    eci = db.compile_pypy_c_extern_funcs()

    graph = graph_of(rposix.makedev, t)

    ccall = graph.startblock.operations[2]
    fnp = ccall.args[0].value
    assert fnp.eci == eci

    assert exported_symbol_in_dylib(fnp._name, eci.libraries[-1])


def test_extern_funcs_support_func():
    from rpython.rlib.rdtoa import dtoa
    def f(x):
        return dtoa(x)

    t = Translation(f, [float], backend='mu')
    t.mutype()

    db = MuDatabase(t.context)
    db.collect_global_defs()
    eci = db.compile_pypy_c_extern_funcs()

    graph = graph_of(dtoa, t)
    ccall = graph.startblock.exits[0].target.exits[0].target.operations[0].args[0].value.graph.startblock.operations[2]
    assert ccall.opname == 'mu_ccall'
    fnp = ccall.args[0].value
    assert fnp.eci == eci

    assert exported_symbol_in_dylib(fnp._name, eci.libraries[-1])


def test_extern_funcs_post_include_bits():
    from rpython.rlib.rmd5 import _rotateLeft
    def f(n, k):
        return _rotateLeft(n, k)
    t = Translation(f, [lltype.Unsigned, lltype.Signed], backend='mu')
    t.mutype()

    db = MuDatabase(t.context)
    db.collect_global_defs()
    eci = db.compile_pypy_c_extern_funcs()

    graph_f = graph_of(f, t)
    ccall = graph_f.startblock.operations[0]
    assert ccall.opname == 'mu_ccall'
    fnp = ccall.args[0].value
    assert fnp.eci == eci

    assert fnp._name.startswith('pypy_macro_wrapper')   # rotateLeft should be wrapped as a 'macro' (rely on inlining)
    assert exported_symbol_in_dylib(fnp._name, eci.libraries[-1])


def test_get_type_name():
    man = MuNameManager()
    assert man.get_type_name(mutype.MU_INT64) == '@i64'
    assert man.get_type_name(mutype.MU_VOID) == '@void'
    assert man.get_type_name(mutype.MuFuncSig(
        [mutype.MU_INT64, mutype.MuArray(mutype.MU_INT8, 10)], [])) == '@sig_i64arr0_'
    Point = mutype.MuStruct('Point', ('x', mutype.MU_INT64), ('y', mutype.MU_INT64))
    assert man.get_type_name(mutype.MuUPtr(Point)) == '@ptrstt0'


def test_get_const_name():
    man = MuNameManager()
    assert man.get_const_name(Constant(mutype.mu_int64(10), mutype.MU_INT64)) == '@0xa_i64'
    assert man.get_const_name(Constant(mutype.mu_double(float('nan')), mutype.MU_DOUBLE)) == '@0x7ff8000000000000_dbl'


def test_assign_mu_name():
    def fac(n):
        if n <= 1:
            return 1
        return n * fac(n - 1)
    t = Translation(fac, [int], backend='mu')
    t.mutype()

    db = MuDatabase(t.context)
    db.collect_global_defs()
    db.assign_mu_name()

    names = db.mu_name_map.values()
    assert '@0x1_i64' in names
    assert '@i64' in names
    assert '@sig_i64_i64' in names
    assert '@fnrsig_i64_i64' in names
    assert '@fac_0' in names
    assert '@fac_0.blk0' in names
    assert '@fac_0.blk0.n_0' in names
