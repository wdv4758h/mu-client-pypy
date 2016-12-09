from rpython.translator.mu.ll2mu import *
from rpython.translator.mu.ll2mu import _init_binop_map, varof
import pytest


def test_map_type_prim():
    ll2mu = LL2MuMapper()
    assert ll2mu.map_type(lltype.Signed) == mutype.MU_INT64
    assert ll2mu.map_type(lltype.Bool) == mutype.MU_INT8

    assert ll2mu.map_type(rffi.INT) == mutype.MU_INT32
    assert ll2mu.map_type(lltype.Void) == mutype.MU_VOID

def test_map_type_addr():
    ll2mu = LL2MuMapper()
    assert ll2mu.map_type(llmemory.Address) == mutype.MU_INT64

def test_map_type_struct():
    ll2mu = LL2MuMapper()
    LLT = lltype.GcStruct('Point', ('x', lltype.Signed), ('y', lltype.Signed))
    MuT = ll2mu.map_type(LLT)

    assert isinstance(MuT, mutype.MuStruct)
    assert len(MuT._names) == 3
    # a GC hash field is added to the front
    assert MuT._names[0] == LL2MuMapper.GC_IDHASH_FIELD[0]
    assert MuT[0] == mutype.MU_INT64
    assert MuT.x == mutype.MU_INT64

    # cached
    assert ll2mu.map_type(LLT) is MuT   # calling a second time return the same object

def test_map_type_hybrid():
    ll2mu = LL2MuMapper()
    from rpython.rtyper.lltypesystem.rstr import STR
    MuT = ll2mu.map_type(STR)

    assert isinstance(MuT, mutype.MuHybrid)
    assert MuT._vartype == mutype._MuMemArray(mutype.MU_INT8)

    A = lltype.GcArray(lltype.Char)
    MuT = ll2mu.map_type(A)
    assert len(MuT._names) == 3 # gc_idhash, length, items
    assert MuT.items.OF == mutype.MU_INT8

def test_map_type_ptr():
    ll2mu = LL2MuMapper()
    Point = lltype.GcStruct('Point', ('x', lltype.Signed), ('y', lltype.Signed))
    Node = lltype.GcForwardReference()
    PtrNode = lltype.Ptr(Node)
    Node.become(lltype.GcStruct("Node", ("payload", Point), ("next", PtrNode)))

    MuT = ll2mu.map_type(PtrNode)
    assert isinstance(MuT, mutype.MuRef)    # GcStruct result in Ref
    assert isinstance(MuT.TO, mutype.MuForwardReference)    # resolve later to break loop
    ll2mu.resolve_ptr_types()
    assert isinstance(MuT.TO, mutype.MuStruct)
    assert MuT.TO.next is MuT   # loop preserved

    RawPoint = lltype.Struct('Point', ('x', lltype.Signed), ('y', lltype.Signed))
    RawPtr = lltype.Ptr(RawPoint)
    assert isinstance(ll2mu.map_type(RawPtr), mutype.MuUPtr)    # non-GCed Struct result in UPtr

    from rpython.rtyper.rclass import OBJECTPTR
    MuT = ll2mu.map_type(OBJECTPTR)
    ll2mu.resolve_ptr_types()
    assert isinstance(MuT.TO.typeptr.TO, mutype.MuStruct)

def test_map_type_funcptr():
    from rpython.rtyper.rclass import OBJECTPTR
    ll2mu = LL2MuMapper()
    MuT = ll2mu.map_type(OBJECTPTR)
    ll2mu.resolve_ptr_types()
    FncRef = MuT.TO.typeptr.TO.instantiate
    Sig = FncRef.Sig
    assert Sig.ARGS == ()
    assert Sig.RESULTS == (MuT, )

# -----------------------------------------------------------------------------
def test_map_value_prim():
    ll2mu = LL2MuMapper()
    assert ll2mu.map_value(10) == mutype.mu_int64(10)
    assert ll2mu.map_value(rffi.INT._type(50)) == mutype.mu_int32(50)
    # XXX: what's the story for negative numbers in Mu? Check with Kunshan
    # for now, assume that negative number will be make unsigned
    assert ll2mu.map_value(rffi.INT._type(-50)) == mutype.mu_int32(4294967246)

    assert ll2mu.map_value(rarithmetic.r_singlefloat(1.5)) == mutype.mu_float(1.5)

    from rpython.rlib.objectmodel import malloc_zero_filled
    assert ll2mu.map_value(malloc_zero_filled) == mutype.mu_int64(0)

    assert ll2mu.map_value('c') == mutype.mu_int8(ord('c'))

def test_map_value_adrofs():
    from rpython.translator.mu.layout import mu_sizeOf, mu_offsetOf, mu_hybsizeOf
    ll2mu = LL2MuMapper()
    assert ll2mu.map_value(llmemory.sizeof(lltype.Char)) == mutype.mu_int64(1)
    S = lltype.GcStruct("Point", ('x', lltype.Signed), ('y', lltype.Signed))
    MuS = ll2mu.map_type(S)
    assert ll2mu.map_value(llmemory.sizeof(S)) == mutype.mu_int64(mu_sizeOf(MuS))
    assert ll2mu.map_value(llmemory.offsetof(S, 'y')) == mu_offsetOf(MuS, 'y')

    A = lltype.GcArray(lltype.Char)
    MuA = ll2mu.map_type(A)
    assert ll2mu.map_value(llmemory.itemoffsetof(A, 10)) == mu_hybsizeOf(MuA, 10)

def test_map_value_stt():
    ll2mu = LL2MuMapper()
    Point = lltype.GcStruct("Point", ('x', lltype.Signed), ('y', lltype.Signed))
    pt = lltype.malloc(Point, zero=True)._obj
    mupt = ll2mu.map_value(pt)
    assert mupt.x == mupt.y == mutype.mu_int64(0)

    # test build parent structure
    Point3D = lltype.GcStruct("Point3D", ('super', Point), ('z', lltype.Signed))
    Point4D = lltype.GcStruct("Point4D", ('super', Point3D), ('w', lltype.Signed))

    pt4d = lltype.malloc(Point4D, zero=True)._obj
    pt3d = pt4d.super
    # map a structure from the middle should return the middle struct but with the whole thing mapped
    mupt3d = ll2mu.map_value(pt3d)
    assert mutype.mutypeOf(mupt3d) == ll2mu.map_type(Point3D)
    assert isinstance(mupt3d.super, mutype._mustruct)
    assert mutype.mutypeOf(mupt3d.super) == ll2mu.map_type(Point)
    mupt4d = mupt3d._parentstructure()
    assert isinstance(mupt4d, mutype._mustruct)
    assert mutype.mutypeOf(mupt4d) == ll2mu.map_type(Point4D)

def test_map_value_varstt():
    ll2mu = LL2MuMapper()

    from rpython.rtyper.lltypesystem.rstr import STR
    s = lltype.malloc(STR, 5, zero=True)._obj
    for i, c in enumerate("hello"):
        s.chars.setitem(i, c)
    s.hash = hash("hello")

    mus = ll2mu.map_value(s)
    assert mus.hash == s.hash
    assert mus.length == 5
    for i in range(5):
        assert mus.chars[i] == ord(s.chars.getitem(i))

def test_map_value_ptr():
    ll2mu = LL2MuMapper()
    Point = lltype.GcStruct("Point", ('x', lltype.Signed), ('y', lltype.Signed))
    PtrPoint = lltype.Ptr(Point)

    nullptr = lltype.nullptr(Point)
    assert ll2mu.map_value(nullptr)._is_null()

    p = lltype.malloc(Point, zero=True)
    r = ll2mu.map_value(p)
    ll2mu.resolve_ptr_values()
    assert isinstance(r, mutype._muref)
    assert mutype.mutypeOf(r._obj) == ll2mu.map_type(Point)

    # a more complicated test, object pointer
    from rpython.rtyper.rclass import OBJECT, OBJECT_VTABLE
    pobj = lltype.malloc(OBJECT, zero=True)
    pvtbl = lltype.malloc(OBJECT_VTABLE, flavor='raw', zero=True)
    pobj.typeptr = pvtbl
    pvtbl.hash = 12345

    r = ll2mu.map_value(pobj)
    ll2mu.resolve_ptr_types()
    ll2mu.resolve_ptr_values()
    assert isinstance(r._obj.typeptr, mutype._muuptr)
    assert isinstance(r._obj.typeptr._obj, mutype._mustruct)
    assert r._obj.typeptr._obj.hash == pvtbl.hash

    lltype.free(pvtbl, flavor='raw')

def test_map_funcptr():
    ll2mu = LL2MuMapper()

    def add1(n):
        return n + 1
    from rpython.rtyper.test.test_llinterp import gengraph
    _, _, g = gengraph(add1, [int])
    fncptr = lltype._func(lltype.FuncType([lltype.Signed], lltype.Signed),
                          graph=g, _name=g.name)._as_ptr()
    fnr = ll2mu.map_value(fncptr)
    assert fnr.graph is g
    assert fnr._name == g.name

    from rpython.rlib.rposix import c_read
    llfncptr = c_read._ptr
    extfnp = ll2mu.map_value(llfncptr)
    assert isinstance(extfnp, mutype._muufuncptr)
    assert extfnp._name == llfncptr._obj._name
    assert extfnp.eci == llfncptr._obj.compilation_info


# -----------------------------------------------------------------------------
# operation map test
def test_mapped_const():
    ll2mu = LL2MuMapper()
    c = ll2mu.mapped_const(True)
    assert c.value == mutype.mu_int8(1)
    assert c.concretetype == mutype.MU_INT8

    d = ll2mu.mapped_const({})
    assert d.value == {}
    assert d.concretetype == mutype.MU_VOID

    t = ll2mu.mapped_const(mutype.MU_INT8)
    assert t.value == mutype.MU_INT8
    assert t.concretetype == mutype.MU_VOID

    e = ll2mu.mapped_const(10)
    assert e.value == mutype.mu_int64(10)
    assert e.concretetype == mutype.MU_INT64

    f = ll2mu.mapped_const(10, rffi.UCHAR)
    assert f.value == mutype.mu_int8(10)
    assert f.concretetype == mutype.MU_INT8

def test_bool_not():
    ll2mu = LL2MuMapper()
    res = varof(mutype.MU_INT8, 'res')
    llop = SpaceOperation('bool_not',
                          [ll2mu.mapped_const(True)],
                          res)
    muops = ll2mu.map_op(llop)
    assert len(muops) == 1
    binop = muops[0]
    assert binop.opname == 'mu_binop'

def test_int_abs():
    ll2mu = LL2MuMapper()
    res = varof(mutype.MU_INT64, 'res')
    llop = SpaceOperation('int_abs',
                          [ll2mu.mapped_const(-125)],
                          res)
    muops = ll2mu.map_op(llop)
    assert len(muops) == 3
    assert [op.opname for op in muops] == ['mu_binop', 'mu_cmpop', 'mu_select']

def test_int_between():
    ll2mu = LL2MuMapper()
    res = varof(ll2mu.map_type(lltype.Bool), 'res')
    llop = SpaceOperation('int_between',
                          [ll2mu.mapped_const(42), varof(mutype.MU_INT64, 'x'), ll2mu.mapped_const(100)],
                          res)
    muops = ll2mu.map_op(llop)
    assert len(muops) == 5
    assert [op.opname for op in muops] == ['mu_cmpop', 'mu_convop', 'mu_cmpop', 'mu_convop', 'mu_binop']

def test_int_mul_ovf():
    ll2mu = LL2MuMapper()
    res = varof(mutype.MU_INT64, 'res')
    llop = SpaceOperation('int_mul_ovf',
                          [varof(mutype.MU_INT64, 'a'), varof(mutype.MU_INT64, 'b')],
                          res)
    muops = ll2mu.map_op(llop)
    assert len(muops) == 1
    op = muops[0]
    assert op.opname == 'mu_binop'
    metainfo = op.args[-1].value
    assert metainfo['status'][0] == 'V'
    assert len(metainfo['status'][1]) == 1
    assert isinstance(metainfo['status'][1][0], Variable)

def test_cast_char_to_int():
    ll2mu = LL2MuMapper()
    res = varof(mutype.MU_INT64, 'res')
    llop = SpaceOperation('cast_char_to_int', [varof(ll2mu.map_type(lltype.Char), 'c')],
                          res)

def test_binop_map():
    llbinops = {
        'char_lt',
        'char_le',
        'char_eq',
        'char_ne',
        'char_gt',
        'char_ge',
        'unichar_eq',
        'unichar_ne',
        'int_add',
        'int_sub',
        'int_mul',
        'int_floordiv',
        'int_mod',
        'int_lt',
        'int_le',
        'int_eq',
        'int_ne',
        'int_gt',
        'int_ge',
        'int_and',
        'int_or',
        'int_lshift',
        'int_rshift',
        'int_xor',
        'uint_add',
        'uint_sub',
        'uint_mul',
        'uint_floordiv',
        'uint_mod',
        'uint_lt',
        'uint_le',
        'uint_eq',
        'uint_ne',
        'uint_gt',
        'uint_ge',
        'uint_and',
        'uint_or',
        'uint_lshift',
        'uint_rshift',
        'uint_xor',
        'float_add',
        'float_sub',
        'float_mul',
        'float_truediv',
        'float_lt',
        'float_le',
        'float_eq',
        'float_ne',
        'float_gt',
        'float_ge',
        'llong_add',
        'llong_sub',
        'llong_mul',
        'llong_floordiv',
        'llong_mod',
        'llong_lt',
        'llong_le',
        'llong_eq',
        'llong_ne',
        'llong_gt',
        'llong_ge',
        'llong_and',
        'llong_or',
        'llong_lshift',
        'llong_rshift',
        'llong_xor',
        'ullong_add',
        'ullong_sub',
        'ullong_mul',
        'ullong_floordiv',
        'ullong_mod',
        'ullong_lt',
        'ullong_le',
        'ullong_eq',
        'ullong_ne',
        'ullong_gt',
        'ullong_ge',
        'ullong_and',
        'ullong_or',
        'ullong_lshift',
        'ullong_rshift',
        'ullong_xor',
        'lllong_add',
        'lllong_sub',
        'lllong_mul',
        'lllong_floordiv',
        'lllong_mod',
        'lllong_lt',
        'lllong_le',
        'lllong_eq',
        'lllong_ne',
        'lllong_gt',
        'lllong_ge',
        'lllong_and',
        'lllong_or',
        'lllong_lshift',
        'lllong_rshift',
        'lllong_xor',
    }
    assert llbinops.difference(_init_binop_map().keys()) == set()    # all covered

def test_malloc_varsize():
    ll2mu = LL2MuMapper()
    Hyb = mutype.MuHybrid('string', ('hash', mutype.MU_INT64), ('length', mutype.MU_INT64), ('chars', mutype.MU_INT8))
    rs = varof(mutype.MuRef(Hyb), "rs")
    llop = SpaceOperation('malloc_varsize', [ll2mu.mapped_const(Hyb),
                                             ll2mu.mapped_const({'flavor': 'gc'}),
                                             ll2mu.mapped_const(10)],
                          rs)
    muops = ll2mu.map_op(llop)
    assert [op.opname for op in muops] == ['mu_newhybrid', 'mu_getiref', 'mu_getfieldiref', 'mu_store']
    assert muops[0].result is rs    # the result is of the first instruction rather than the last


def test_malloc_varsize_raw():
    ll2mu = LL2MuMapper()
    Hyb = mutype.MuHybrid('string', ('hash', mutype.MU_INT64), ('length', mutype.MU_INT64), ('chars', mutype.MU_INT8))
    rs = varof(mutype.MuUPtr(Hyb), "rs")
    llop = SpaceOperation('malloc_varsize', [ll2mu.mapped_const(Hyb),
                                             ll2mu.mapped_const({'flavor': 'raw'}),
                                             ll2mu.mapped_const(10)],
                          rs)
    muops = ll2mu.map_op(llop)
    assert [op.opname for op in muops] == ['mu_binop', 'mu_binop', 'mu_ccall', 'mu_getfieldiref', 'mu_store']


def test_setarrayitem():
    ll2mu = LL2MuMapper()
    Hyb = mutype.MuHybrid('string', ('hash', mutype.MU_INT64), ('length', mutype.MU_INT64), ('chars', mutype.MU_INT8))
    rs = varof(mutype.MuRef(Hyb), "rs")
    res = Variable('res')
    llop = SpaceOperation('setarrayitem', [rs, ll2mu.mapped_const(5), ll2mu.mapped_const('c')], res)
    muops = ll2mu.map_op(llop)
    assert [op.opname for op in muops] == ['mu_getiref', 'mu_getvarpartiref', 'mu_shiftiref', 'mu_store']

def test_getinteriorarraysize():
    ll2mu = LL2MuMapper()
    Str = mutype.MuHybrid('string', ('hash', mutype.MU_INT64), ('length', mutype.MU_INT64), ('chars', mutype.MU_INT8))
    ps = varof(mutype.MuUPtr(Str), 'rs')
    res = varof(mutype.MU_INT64, 'res')
    llop = SpaceOperation('getinteriorarraysize', [ps, Constant('chars', mutype.MU_VOID)], res)
    muops = ll2mu.map_op(llop)
    assert [op.opname for op in muops] == ['mu_getfieldiref', 'mu_load']
    assert isinstance(muops[0].result.concretetype, mutype.MuUPtr)

def test_setinteriorfield():
    ll2mu = LL2MuMapper()
    Stt = mutype.MuStruct('point', ('x', mutype.MU_INT64), ('y', mutype.MU_INT64))
    Hyb = mutype.MuHybrid('array', ('length', mutype.MU_INT64), ('points', Stt))
    rh = varof(mutype.MuRef(Hyb))
    res = varof(mutype.MU_VOID)
    llop = SpaceOperation('setinteriorfield', [rh, Constant('points', mutype.MU_VOID),
                                               Constant(5, mutype.MU_INT64), Constant('x', mutype.MU_VOID),
                                               Constant(42, mutype.MU_INT64)], res)
    muops = ll2mu.map_op(llop)
    assert [op.opname for op in muops] == ['mu_getiref', 'mu_getvarpartiref', 'mu_shiftiref', 'mu_getfieldiref', 'mu_store']


def test_ptr_nonzero():
    ll2mu = LL2MuMapper()
    Stt = mutype.MuStruct('point', ('x', mutype.MU_INT64), ('y', mutype.MU_INT64))
    rs = varof(mutype.MuRef(Stt))
    res = varof(mutype.MU_INT8)
    muops = ll2mu.map_op(SpaceOperation('ptr_nonzero', [rs], res))
    assert [op.opname for op in muops] == ['mu_cmpop', 'mu_convop']

def test_raw_memcopy():
    ll2mu = LL2MuMapper()
    VOIDP = ll2mu.map_type(rffi.VOIDP)
    src = varof(mutype.MU_INT64, 'src')
    dst = varof(mutype.MU_INT64, 'dst')
    sz = varof(mutype.MU_INT64, 'sz')
    llop = SpaceOperation('raw_memcopy', [src, dst, sz], varof(mutype.MU_VOID))
    muops = ll2mu.map_op(llop)
    assert [op.opname for op in muops] == ['mu_convop', 'mu_convop', 'mu_ccall']
    ccall = muops[-1]
    assert ccall.args[0].value._name == 'memcpy'
    assert muops[0].args[-1] is src
    src_cast = muops[0].result
    assert muops[1].args[-1] is dst
    dst_cast = muops[1].result
    assert ccall.args[1] is dst_cast and ccall.args[2] is src_cast

def test_gc_identityhash():
    from rpython.translator.interactive import Translation

    def f(pobj):
        return lltype.identityhash(pobj)

    Point = lltype.GcStruct('Point', ('x', lltype.Signed), ('y', lltype.Signed))
    PointPtr = lltype.Ptr(Point)

    t = Translation(f, [PointPtr])
    t.rtype()

    ll2mu = LL2MuMapper(t.context.rtyper)

    llop = t.context.graphs[0].startblock.operations[0]
    print llop
    assert llop.opname == 'gc_identityhash'

    llop.args[0].concretetype = ll2mu.map_type(llop.args[0].concretetype)
    llop.result.concretetype = ll2mu.map_type(llop.result.concretetype)

    muops = ll2mu.map_op(llop)
    assert [op.opname for op in muops] == ['mu_call']

    call = muops[0]
    callee_c = call.args[0]
    assert isinstance(callee_c.concretetype, mutype.MuFuncRef)
    assert isinstance(callee_c.value, mutype._mufuncref)
    callee = callee_c.value
    assert callee.graph in t.context.graphs
    assert 'mu_getgcidhash' in [op.opname for _, op in callee.graph.iterblockops()]
    assert 'mu_setgcidhash' in [op.opname for _, op in callee.graph.iterblockops()]


def test_force_cast():
    Stt = mutype.MuStruct('point', ('x', mutype.MU_INT64), ('y', mutype.MU_INT64))

    ll2mu = LL2MuMapper()
    muops = ll2mu.map_op(SpaceOperation('force_cast', [varof(mutype.MuRef(Stt))], varof(mutype.MU_INT64)))
    assert [op.opname for op in muops] == ['mu_comminst', 'mu_convop']    # pin, then PTRCAST

    with pytest.raises(AssertionError):
        ll2mu.map_op(SpaceOperation('force_cast', [varof(mutype.MU_INT64)], varof(mutype.MuRef(Stt))))
    muops = ll2mu.map_op(SpaceOperation('force_cast', [varof(mutype.MU_INT64)], varof(mutype.MuUPtr(Stt))))
    assert [op.opname for op in muops] == ['mu_convop']

    with pytest.raises(AssertionError):
        ll2mu.map_op(SpaceOperation('force_cast', [varof(mutype.MuRef(Stt))], varof(mutype.MuUPtr(mutype.MU_INT64))))
    muops = ll2mu.map_op(SpaceOperation('force_cast', [varof(mutype.MuRef(Stt))], varof(mutype.MuRef(mutype.MU_INT64))))
    assert [op.opname for op in muops] == ['mu_convop']

    # TODO: test more cases for force_cast? Maybe it will be easier with a graph interpreter