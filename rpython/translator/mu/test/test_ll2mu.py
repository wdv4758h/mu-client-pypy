from rpython.translator.mu.ll2mu import *


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

def check_muop(muop):
    for arg in muop.args:
        assert isinstance(arg, (Variable, Constant))
        assert isinstance(arg.concretetype, mutype.MuType)

    def check_flag(const, cls):
        assert isinstance(const, Constant)
        assert const.concretetype == mutype.MU_INT32
        flags = filter(lambda k: k.isupper(), cls.__dict__.keys())
        assert any(const.value == getattr(cls, flag) for flag in flags)

    res = muop.result
    args = muop.args
    if muop.opname == 'mu_binop':
        """
        The arguments of mu_binops are:
            0: optr(Constant(rmu.MuBinOptr)>
            1: operand 1
            2: operand 2
            3: metainfo(Constant(dict))
                - 'exc': exception clause
                - 'status': (ORed rmu.BinOpStatus, list of result Variables)
        """
        assert len(args) == 4
        check_flag(args[0], rmu.MuBinOptr)

        assert args[1].concretetype == args[2].concretetype == res.concretetype

        assert isinstance(args[3], Constant)
        assert isinstance(args[3].value, dict)
        d = args[3].value
        if 'exc' in d:
            assert isinstance(d['exc'], tuple)
            assert isinstance(d['exc'][0], Link)
            assert isinstance(d['exc'][1], Link)
        if 'status' in d:
            assert isinstance(d['status'][0], mutype.mu_int32)
            assert isinstance(d['status'][1], list)
            for v in d['status'][1]:
                assert isinstance(v, Variable)

    elif muop.opname == 'mu_cmpop':
        """
        The arguments of mu_cmpop are:
            0: optr(Constant(rmu.MuCmpOptr)>
            1: operand 1
            2: operand 2
        """
        assert len(args) == 3
        check_flag(args[0], rmu.MuCmpOptr)

        assert args[1].concretetype == args[2].concretetype
        assert res.concretetype == mutype.MU_INT1

    elif muop.opname == 'mu_convop':
        """
        The arguments of mu_convop are:
        0: optr(Constant(rmu.MuConvOptr)>
        1: operand
        2: to_ty (Constant(MuType))
        """
        assert len(args) == 3
        check_flag(args[0], rmu.MuConvOptr)

        assert isinstance(args[2], Constant)
        assert isinstance(args[2].value, mutype.MuType)
        assert res.concretetype == args[2].value

    elif muop.opname == 'mu_select':
        assert len(args) == 3
        assert args[0].concretetype == mutype.MU_INT1
        assert args[1].concretetype == args[2].concretetype == res.concretetype

    elif muop.opname == 'mu_branch':
        assert len(args) == 1
        assert isinstance(args[0], Constant)
        assert isinstance(args[0].value, Link)

    elif muop.opname == 'mu_branch2':
        assert len(args) == 3
        assert args[0].concretetype == mutype.MU_INT1
        assert isinstance(args[1], Constant)
        assert isinstance(args[1].value, Link)
        assert isinstance(args[2], Constant)
        assert isinstance(args[2].value, Link)

    elif muop.opname == 'mu_switch':
        raise NotImplementedError
    elif muop.opname == 'mu_call':
        raise NotImplementedError
    elif muop.opname == 'mu_tailcall':
        raise NotImplementedError
    elif muop.opname == 'mu_ret':
        raise NotImplementedError
    elif muop.opname == 'mu_throw':
        raise NotImplementedError
    elif muop.opname == 'mu_extractvalue':
        raise NotImplementedError
    elif muop.opname == 'mu_insertvalue':
        raise NotImplementedError
    elif muop.opname == 'mu_extractelement':
        raise NotImplementedError
    elif muop.opname == 'mu_insertelement':
        raise NotImplementedError
    elif muop.opname == 'mu_new':
        raise NotImplementedError
    elif muop.opname == 'mu_alloca':
        raise NotImplementedError
    elif muop.opname == 'mu_newhybrid':
        raise NotImplementedError
    elif muop.opname == 'mu_allocahybrid':
        raise NotImplementedError
    elif muop.opname == 'mu_getiref':
        raise NotImplementedError
    elif muop.opname == 'mu_getfieldiref':
        raise NotImplementedError
    elif muop.opname == 'mu_getelemiref':
        raise NotImplementedError
    elif muop.opname == 'mu_shiftiref':
        raise NotImplementedError
    elif muop.opname == 'mu_getvarpartiref':
        raise NotImplementedError
    elif muop.opname == 'mu_load':
        raise NotImplementedError
    elif muop.opname == 'mu_store':
        raise NotImplementedError
    elif muop.opname == 'mu_trap':
        raise NotImplementedError
    elif muop.opname == 'mu_ccall':
        raise NotImplementedError
    elif muop.opname == 'mu_comminst':
        raise NotImplementedError

def test_bool_not():
    ll2mu = LL2MuMapper()
    llop = SpaceOperation('bool_not',
                          [ll2mu.mapped_const(True)],
                          ll2mu.var('res', mutype.MU_INT8))
    muops = ll2mu.map_op(llop)
    assert len(muops) == 1
    binop = muops[0]
    assert binop.opname == 'mu_binop'

    for op in muops:
        check_muop(op)