from rpython.flowspace.model import *
from rpython.translator.mu.mutyper import *
from rpython.translator.interactive import Translation

def graph_of(f, t):
    return t.context.annotator.bookkeeper.getdesc(f).getuniquegraph()

def test_prune():
    def g(x):
        return x * (x + 1)
    def f(x):
        return 3 * g(x) + 8

    t = Translation(f, [int])
    t.rtype()
    graphs = t.context.graphs
    graph_f = graph_of(f, t)

    assert len(prune(graph_f)) == 2     # pruned out ll_runtime_type_info, ll_issubclass, ll_type
    t.backendopt()  # this should inline g
    assert len(prune(graph_f)) == 1     # pruned g


def test_prune_preserve_func_references():
    def add1(x): return x + 1
    def add2(x): return x + 2
    def add3(x): return x + 3
    fncs = {
        '1': add1,
        '2': add2,
        '3': add3
    }

    def f(x, k):
        g = fncs[str(k)]
        return g(x)

    t = Translation(f, [int, int])
    t.rtype()
    graphs = t.context.graphs
    graph_f = graph_of(f, t)
    graph_add1 = graph_of(add1, t)
    graph_add2 = graph_of(add2, t)
    graph_add3 = graph_of(add3, t)

    assert len(prune(graph_f)) < len(graphs)
    assert graph_add1 in graphs
    assert graph_add2 in graphs
    assert graph_add3 in graphs


def test_specialise_arg():
    from rpython.translator.translator import TranslationContext
    mutyper = MuTyper(TranslationContext())

    # Variable
    Point = lltype.GcStruct('Point', ('x', lltype.Signed), ('y', lltype.Signed))
    v = mutyper.specialise_arg(varof(lltype.Ptr(Point)))
    assert isinstance(v.concretetype.TO, mutype.MuStruct)   # resolved

    # translatable Constants
    c_1 = mutyper.specialise_arg(Constant(1, lltype.Signed))
    assert c_1.concretetype == mutype.MU_INT64
    assert isinstance(c_1.value, mutype.mu_int64)
    # AddressOffsets
    ofs = llmemory.ItemOffset(lltype.Char)
    c_sym = mutyper.specialise_arg(Constant(ofs, ofs.lltype()))
    assert c_sym.concretetype == mutype.MU_INT64
    assert isinstance(c_sym.value, mutype.mu_int64)  # calculated

    # non-translatable Constants
    c_d = mutyper.specialise_arg(Constant({'flavor': 'raw'}, lltype.Void))
    assert c_d.concretetype == mutype.MU_VOID
    assert c_d.value == {'flavor': 'raw'}

    # type Constants
    c_t = mutyper.specialise_arg(Constant(Point, lltype.Void))
    assert c_t.concretetype == mutype.MU_VOID
    assert isinstance(c_t.value, mutype.MuType)

    # heap Constants
    ptr = lltype.malloc(Point)
    ptr.x = 42
    ptr.y = 53
    c = mutyper.specialise_arg(Constant(ptr, lltype.typeOf(ptr)))
    assert isinstance(c.concretetype, mutype.MuGlobalCell)
    assert isinstance(c.concretetype.TO, mutype.MuRef)
    assert isinstance(c.concretetype.TO.TO, mutype.MuStruct)
    assert isinstance(c.value, mutype._muglobalcell)
    assert isinstance(c.value._obj, mutype._muref)
    assert isinstance(c.value._obj._obj, mutype._mustruct)
    assert c.value._obj._obj.x == 42
    assert c.value._obj._obj.y == 53


def test_specialise_op():
    def f(s):
        return s.x

    Point = lltype.GcStruct('Point', ('x', lltype.Signed), ('y', lltype.Signed))
    t = Translation(f, [lltype.Ptr(Point)])
    t.rtype()
    mutyper = MuTyper(t.context)

    graph_f = graph_of(f, t)
    op = graph_f.startblock.operations[0]
    assert op.opname == 'getfield'

    muops = mutyper.specialise_operation(op)
    assert [op.opname for op in muops] == ['mu_getiref', 'mu_getfieldiref', 'mu_load']
    for muop in muops:
        for arg in muop.args:
            if isinstance(arg, (Variable, Constant)):
                assert isinstance(arg.concretetype, mutype.MuType)
            if isinstance(arg, Constant):
                if arg.concretetype is not mutype.MU_VOID:
                    assert mutype.mutypeOf(arg.value) == arg.concretetype


def test_specialise_block():
    def fac(x):
        if x <= 1:
            return 0
        return x * fac(x - 1)

    t = Translation(fac, [lltype.Signed])
    t.rtype()
    t.backendopt()

    mutyper = MuTyper(t.context)

    graph_fac = graph_of(fac, t)
    blk = graph_fac.startblock
    assert len(blk.exits) == 2

    mutyper.specialise_block(blk)

    for arg in blk.inputargs:
        assert isinstance(arg.concretetype, mutype.MuType)
    for op in blk.operations:
        if op.opname != 'same_as':
            assert op.opname.startswith('mu_')

    op = blk.operations[-1]
    assert op.opname == 'mu_branch2'
    assert blk.operations[-2].opname == 'mu_cmpop'  # convert to MU_INT1

    # multiple exits -> switch
    def f(x):
        if x == 1:
            return 1
        elif x == 2:
            return 5
        elif x == 3:
            return 10
        elif x == 4:
            return 20
        else:
            return 100
    t = Translation(f, [lltype.Signed])
    t.rtype()
    t.backendopt()

    mutyper = MuTyper(t.context)

    graph_f = graph_of(f, t)
    blk = graph_f.startblock
    assert len(blk.exits) > 2

    mutyper.specialise_block(blk)

    assert blk.operations[-1].opname == 'mu_switch'

