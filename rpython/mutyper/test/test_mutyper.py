from rpython.translator.mu.preps import prepare
from ..mutyper import MuTyper
from rpython.rtyper.lltypesystem import lltype as llt
from ..muts import mutype as mut
from rpython.rtyper.lltypesystem.rstr import STR
from rpython.flowspace.model import Constant, Variable
from ..muts.muentity import MuGlobalCell, MuName
from rpython.rtyper.test.test_llinterp import gengraph
from ..ll2mu import *
from ..tools.textgraph import print_graph


def test_ldgcell():
    def f(s):
        return s + "hello"

    t, _, g = gengraph(f, [str])
    print_graph(g)
    typer = MuTyper(t)
    typer.specialise(g)
    op = g.startblock.operations[0]
    assert op.opname == 'LOAD'
    assert isinstance(op.loc, MuGlobalCell)
    assert g.startblock.operations[1].opname == 'CALL'


def test_gcellnodup():
    def main(argv):
        return int(argv[0]) * 10

    t, _, g = gengraph(main, [[str]], backendopt=True)

    t.graphs = prepare(t.graphs, g)

    graph = g.startblock.operations[-2].args[0].value._obj.graph
    print_graph(graph)

    mutyper = MuTyper(t)
    for _g in t.graphs:
        mutyper.specialise(_g)

    print mutyper.ldgcells
    assert len(mutyper.ldgcells) == 2


def test_argtransform():
    def fac(n):
        if n in (0, 1):
            return 1
        return n * fac(n - 1)

    t, _, g = gengraph(fac, [int])
    print_graph(g)

    typer = MuTyper(t)
    typer.specialise(g)

    assert g.mu_name == MuName("fac")
    assert g.mu_type == mut.MuFuncRef(mut.MuFuncSig((mut.int64_t,), (mut.int64_t,)))
    assert g.startblock.mu_name == MuName("blk0", g)
    blk = g.startblock.exits[0].target
    op = blk.operations[1]  # v41 = direct_call((<* fn fac>), v40)
    assert op.callee == g
    assert op.result.mu_name == MuName(op.result.name, blk)
    assert op.result.mu_type == mut.int64_t


def test_typesandconsts():
    def fac(n):
        if n in (0, 1):
            return 1
        return n * fac(n - 1)

    t, _, g = gengraph(fac, [int])
    print_graph(g)

    typer = MuTyper(t)
    typer.specialise(g)

    # assert len(typer.gblcnsts) == 2
    assert len(typer.ldgcells) == 0
    # assert len(typer.gbltypes) == 4     # (funcref<(i64, i64)->i1>, funcref<(i64)->i64>, i64, i1)


# def test_crush():
#     def main(argv):
#         return int(argv[0]) * 10
#
#     t, _, g = gengraph(main, [[str]], backendopt=True)
#
#     from rpython.translator.mu.preps import prepare
#     t.graphs = prepare(t.graphs, g)
#
#     mutyper = MuTyper()
#     graph = g.startblock.operations[-2].args[0].value._obj.graph
#     mutyper.specialise(graph)


def test_pick_out_gen_const():
    def f(x):
        return - x

    t, _, g = gengraph(f, [int])
    print_graph(g)

    mutyper = MuTyper(t)
    mutyper.specialise(g)
    # assert len(mutyper.gblcnsts) == 1   # 0


def test_externfnc():
    def f(s):
        return s + '_suffix'

    t, _, g_f = gengraph(f, [str], backendopt=True)
    t.graphs = prepare(t.graphs, g_f)   # remove the ({'flavor': 'gc'}) from mallocs
    g = g_f.startblock.operations[0].args[0].value._obj.graph
    # print_graph(g)

    blk = g.startblock.exits[1].target.exits[1].target
    # ------------------------------------------------------
    # blk_4
    # input: [dst_0, src_0, length_10, len2_0, s2_3]
    # operations:
    #     v94 = debug_assert((True), ('copystrc: negative srcstart'))
    #     v95 = int_add((0), length_10)
    #     v96 = getinteriorarraysize(src_0, ('chars'))
    #     v97 = int_le(v95, v96)
    #     v98 = debug_assert(v97, ('copystrc: src ovf'))
    #     v99 = debug_assert((True), ('copystrc: negative dststart'))
    #     v100 = int_add((0), length_10)
    #     v101 = getinteriorarraysize(dst_0, ('chars'))
    #     v102 = int_le(v100, v101)
    #     v103 = debug_assert(v102, ('copystrc: dst ovf'))
    #     v104 = cast_ptr_to_adr(src_0)
    #     v105 = adr_add(v104, (< <FieldOffset <GcStru...r> 0> >))
    #     v106 = cast_ptr_to_adr(dst_0)
    #     v107 = adr_add(v106, (< <FieldOffset <GcStru...r> 0> >))
    #     v108 = int_mul((<ItemOffset <Char> 1>), length_10)
    #     v109 = raw_memcopy(v105, v107, v108)
    #     v110 = keepalive(src_0)
    #     v111 = keepalive(dst_0)
    #     v112 = int_ge(len2_0, (0))
    # switch: v112
    # exits: [('blk_3', [(<* struct object_vtabl...=... }>), (<* struct object { typ...=... }>)]),
    #           ('blk_5', [dst_0, length_10, s2_3, len2_0])]
    # ------------------------------------------------------
    mutyper = MuTyper(t)
    blk.mu_name = MuName("blk_4", g)
    mutyper.specialise(g)

    for op in blk.operations:
        print op


def test_llhelperfunc():
    class Cls:
        pass
    a = Cls()
    b = Cls()
    dic = {a: 1, b: 2}
    def lookup(obj):
        return dic[obj]

    t, _, g_lu = gengraph(lookup, [Cls])
    t.graphs = prepare(t.graphs, g_lu)
    print_graph(g_lu)
    g = g_lu.startblock.operations[1].args[0].value._obj0.graph.startblock.operations[1].args[
        0].value._obj0.graph
    print_graph(g)
    blk = g.startblock.exits[1].target
    op = blk.operations[0]      # gc_identityhash(inst)

    mutyper = MuTyper(t)
    muops = mutyper.specialise_op(op, blk)
