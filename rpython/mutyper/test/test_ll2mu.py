import pytest
from rpython.mutyper.muts.muentity import MuName
from rpython.mutyper.mutyper import MuTyper, muni
from rpython.translator.mu.preps import prepare
from ..ll2mu import ll2mu_ty, ll2mu_val, ll2mu_op
from rpython.rtyper.lltypesystem import lltype as ll
from rpython.mutyper.muts import mutype as mu
from rpython.mutyper.muts import muops
from rpython.rtyper.lltypesystem.rstr import STR
from rpython.rtyper.rclass import OBJECT
from rpython.rtyper.test.test_llinterp import gengraph
from rpython.flowspace.model import SpaceOperation, Variable, Constant
from ..tools.textgraph import print_graph


def test_ll2mu_ty():
    assert ll2mu_ty(ll.Signed) == mu.int64_t

    S = ll2mu_ty(STR)
    assert isinstance(S, mu.MuHybrid)
    assert hasattr(S, 'length')
    assert S.length == mu.int64_t
    assert S.hash == mu.int64_t
    assert S.chars == mu.int8_t

    PS = ll2mu_ty(ll.Ptr(STR))
    assert isinstance(PS, mu.MuRef)
    assert PS.TO == S

    OBJ = ll2mu_ty(OBJECT)
    assert OBJ.typeptr.TO.instantiate.Sig.RTNS[0].TO == OBJ

    A = ll2mu_ty(ll.Array(ll.Char))
    assert isinstance(A, mu.MuHybrid)

    FA = ll2mu_ty(ll.FixedSizeArray(ll.Char, 10))
    assert isinstance(FA, mu.MuArray)
    assert FA.length == 10


def test_ll2mu_val():
    assert ll2mu_val(1) == mu._muprimitive(mu.int64_t, 1)

    string = "hello"
    ll_ps = ll.malloc(STR, len(string))
    ll_ps.hash = hash(string)
    for i in range(len(string)):
        ll_ps.chars[i] = string[i]

    mu_rs = ll2mu_val(ll_ps)
    assert isinstance(mu_rs, mu._muref)
    mu_irs = mu_rs._getiref()
    assert isinstance(mu_irs._obj, mu._muhybrid)
    assert isinstance(mu_irs.length._obj, mu._muprimitive)
    assert mu_irs.hash._obj.val == ll_ps.hash
    assert mu_irs.length._obj.val == len(string)
    for i in range(len(string)):
        assert mu_irs.chars[i]._obj.val == ord(string[i])


def test_ll2mu_fncptr():
    def fac(n):
        if n in (0, 1):
            return 1
        return n * fac(n - 1)

    def f(x):
        return x + fac(x)

    _, _, g = gengraph(f, [int])

    op = g.startblock.operations[0]
    assert op.opname == 'direct_call'
    mut = ll2mu_ty(op.args[0].concretetype)
    muv = ll2mu_val(op.args[0].value)
    assert isinstance(mut, mu.MuFuncRef)
    assert isinstance(muv, mu._mufuncref)
    assert muv.graph == op.args[0].value._obj.graph

    # An example of no graphs.
    def fac2(n):
        if n in (0, 1):
            v = 1
        else:
            v = n * fac(n - 1)
        print v
        return v

    _, _, g2 = gengraph(fac2, [int])

    fncptr_write = \
        g2.startblock.exits[1].target.operations[2].args[0].value._obj.graph.startblock.exits[0].target. \
            operations[0].args[0].value._obj.graph.startblock.operations[0].args[0].value._obj.graph. \
            startblock.operations[13].args[0].value._obj.graph.startblock.exits[0].target.exits[0].target. \
            exits[0].target.exits[0].target.exits[0].target.exits[0].target.exits[0].target.exits[0].target. \
            operations[12].args[0].value._obj.graph.startblock.operations[2].args[0].value
    muv = ll2mu_val(fncptr_write)
    assert muv.fncname == "write"
    assert muv.graph is None
    assert muv.compilation_info == fncptr_write._obj.compilation_info


def test_ll2muop_maps():
    from ..ll2mu import __primop_map, __cast_map, __spec_cast_map
    from rpython.rtyper.lltypesystem.lloperation import LL_OPERATIONS

    # The keys in these maps must be valid LLOps.
    for key in __primop_map:
        assert key in LL_OPERATIONS
    for key in __cast_map:
        assert key in LL_OPERATIONS
    for key in __spec_cast_map:
        assert key in LL_OPERATIONS


def test_ll2muop_1():
    def fac(n):
        if n in (0, 1):
            return 1
        return n * fac(n - 1)

    _, _, g = gengraph(fac, [int])
    # == == == == == == == == == == == == == == == == == == == == == == == ==
    # (rpython.mutyper.test.test_mutyper:30)fac
    # ------------------------
    # blk0
    # input: [n_0]
    # operations:
    # v36 = direct_call(( < * fn _ll_equal__Signe...Signed >), n_0, (0))
    # v37 = direct_call(( < * fn _ll_equal__Signe...Signed >), n_0, (1))
    # v38 = int_or(v36, v37)
    # v39 = same_as(v38)
    # switch: v39
    # exits: [('blk@1', [n_0]), ('blk@2', [(1)])]
    # ------------------------
    # blk1
    # input: [n_1]
    # operations:
    # v40 = int_sub(n_1, (1))
    # v41 = direct_call(( < * fn fac >), v40)
    # v42 = int_mul(n_1, v41)
    # exits: [('blk@2', [v42])]
    # ------------------------
    # blk2
    # input: [v43]
    # operations:
    # exits: []
    # == == == == == == == == == == == == == == == == == == == == == == == ==
    op = g.startblock.operations[2]
    assert op.opname == 'int_or'
    typer = MuTyper()
    op.result = typer.proc_arg(op.result, g.startblock)
    typer.proc_arglist(op.args, g.startblock)

    muop = ll2mu_op(op)[0]
    assert muop.opname == 'OR'
    assert muop.op1 == op.args[0]
    assert muop.op2 == op.args[1]
    assert muop.result == op.result

    op = g.startblock.operations[0]
    assert op.opname == 'direct_call'
    graph = op.args[0].value._obj.graph
    op.result = typer.proc_arg(op.result, g.startblock)
    typer.proc_arglist(op.args, g.startblock)

    muop = ll2mu_op(op)[0]
    assert muop.opname == 'CALL'
    assert muop.callee == graph


def _search_op(g, opname, searched=list()):
    searched.append(g)
    for _, op in g.iterblockops():
        if op.opname == opname:
            yield op
        elif op.opname == 'direct_call':
            graph = op.args[0].value._obj.graph
            if graph not in searched:
                try:
                    rtn = _search_op(graph, opname, searched).next()
                    yield rtn
                except StopIteration:
                    pass


def test_ll2muop_2():
    def f(s):
        d = {'abc': 23, 'efv': 87}
        if s in d:
            return d[s]
        return 0

    _, _, g = gengraph(f, [str])
    opgen = _search_op(g, 'getinteriorfield')
    op = opgen.next()
    # v79 = getinteriorfield(s_0, ('chars'), (0))

    typer = MuTyper()
    op.result = typer.proc_arg(op.result, g.startblock)
    typer.proc_arglist(op.args, g.startblock)

    muops = ll2mu_op(op)
    assert map(lambda op: op.opname, muops) == ['GETIREF', 'GETVARPARTIREF', 'SHIFTIREF', 'LOAD']

    opgen = _search_op(g, 'getinteriorarraysize')
    op = opgen.next()
    # len1_0 = getinteriorarraysize(v80, ('chars'))

    op.result = typer.proc_arg(op.result, g.startblock)
    typer.proc_arglist(op.args, g.startblock)
    muops = ll2mu_op(op)
    assert map(lambda op: op.opname, muops) == ['GETIREF', 'GETFIELDIREF', 'LOAD']


def test_crush():
    def main(argv):
        return int(argv[0]) * 10

    t, _, g = gengraph(main, [[str]], backendopt=True)

    t.graphs = prepare(t.graphs, g)
    graph = g.startblock.operations[-2].args[0].value._obj.graph

    cst = graph.startblock.exits[0].args[0]
    v = cst.value._obj.rtti
    print v, v._TYPE
    with pytest.raises(NotImplementedError):
        ll2mu_val(v)


def test_address():
    def f(s):
        return s + '_suffix'

    t, _, g_f = gengraph(f, [str], backendopt=True)

    g = g_f.startblock.operations[0].args[0].value._obj.graph
    # print_graph(g)

    blk = g.startblock.exits[1].target.exits[1].target
    blk.mu_name = MuName('blk_4', g)
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
    op = blk.operations[10]     # v104 = cast_ptr_to_adr(src_0)

    mutyper = MuTyper()
    muop = mutyper.specialise_op(op, blk)[0]
    assert isinstance(op.result.mu_type, mu.MuUPtr)
    assert op.result.mu_type.TO == op.args[0].mu_type.TO
    assert isinstance(muop, muops.NATIVE_PIN)
    assert mutyper._addrder.find_root(op.result) == op.args[0].concretetype

    assert isinstance(ll2mu_op(blk.operations[16])[0], muops.NATIVE_UNPIN)

    op = blk.operations[11]     # v105 = adr_add(v104, (< <FieldOffset <GcStru...r> 0> >))
    assert isinstance(op.args[0].mu_type, mu.MuUPtr)
    oplist = mutyper.specialise_op(op, blk)
    assert len(oplist) == 2
    assert 'GETVARPARTIREF PTR' in str(oplist[0])
    assert 'SHIFTIREF PTR' in str(oplist[1])

    for op in blk.operations[12:14]:
        mutyper.specialise_op(op, blk)

    op = blk.operations[14]     # v108 = int_mul((<ItemOffset <Char> 1>), length_10)
    mutyper.proc_arglist(op.args, blk)
    assert op.args[0].value == mu.int64_t(1)
    op.result = mutyper.proc_arg(op.result, blk)
    oplist = ll2mu_op(op)
    assert len(oplist) == 1
    assert 'MUL <@i64> @1 %length' in str(oplist[0])

    op = blk.operations[15]     # v109 = raw_memcopy(v105, v107, v108)
    assert op.args[0]
    muop = mutyper.specialise_op(op, blk)[0]
    assert muop.opname == 'CCALL'
    assert muop.callee == muni.c_memcpy
