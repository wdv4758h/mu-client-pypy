from rpython.mutyper.mutyper import MuTyper
from rpython.mutyper.tools.textgraph import print_graph
from rpython.rtyper.test.test_llinterp import gengraph
from rpython.translator.mu.preps import prepare
from ..hail import _HAILName, HAILGenerator
from rpython.mutyper.muts.mutype import *
from rpython.mutyper.muts.muentity import *
from StringIO import StringIO
from rpython.rtyper.lltypesystem import lltype as ll
from rpython.rtyper.lltypesystem.rstr import STR
from rpython.mutyper.ll2mu import ll2mu_val, ll2mu_ty


def test_linkedlist():
    Node = MuStruct('Node')
    Node._setfields([('data', int64_t), ('nxt', MuRef(Node))])

    nd1 = new(Node)
    nd2 = new(Node)
    gcell1 = MuGlobalCell(mu_typeOf(nd1))
    gcell2 = MuGlobalCell(mu_typeOf(nd2))

    gcell1._obj = nd1
    gcell2._obj = nd2

    iref_nd1 = nd1._getiref()
    iref_nd2 = nd2._getiref()
    iref_nd1.data._obj = int64_t(1)
    iref_nd1.nxt._obj = nd2
    iref_nd2.data._obj = int64_t(2)
    iref_nd2.nxt._obj = nd1



    hailgen = HAILGenerator()
    hailgen.add_gcell(gcell1)
    assert len(hailgen._refs) == 2
    assert isinstance(hailgen._refs[nd2._obj0], _HAILName)
    assert hailgen.gcells[gcell1] == hailgen._refs[nd1._obj0]

    hailgen.add_gcell(gcell2)
    assert len(hailgen._refs) == 2
    assert isinstance(hailgen._refs[nd2._obj0], _HAILName)
    assert hailgen.gcells[gcell2] == hailgen._refs[nd2._obj0]

    strio = StringIO()
    hailgen.codegen(strio)
    out = strio.getvalue()
    strio.close()

    print out
    assert '.new $refsttNode_0 <@sttNode>' in out
    assert '.new $refsttNode_1 <@sttNode>' in out
    assert '.init $refsttNode_0 = {1 $refsttNode_1}' in out
    assert '.init $refsttNode_1 = {2 $refsttNode_0}' in out
    assert '.init @gclrefsttNode_0 = $refsttNode_0' in out
    assert '.init @gclrefsttNode_1 = $refsttNode_1' in out


def test_string():
    string = "hello"
    ll_ps = ll.malloc(STR, len(string))
    ll_ps.hash = hash(string)
    for i in range(len(string)):
        ll_ps.chars[i] = string[i]

    mu_t = ll2mu_ty(ll_ps._TYPE)
    mu_rs = ll2mu_val(ll_ps)

    gcell = MuGlobalCell(mu_t)
    gcell._obj = mu_rs

    hailgen = HAILGenerator()
    hailgen.add_gcell(gcell)
    strio = StringIO()
    hailgen.codegen(strio)
    out = strio.getvalue()
    strio.close()

    print out
    ref_name = hailgen.gcells[gcell]
    alloc_str = '.newhybrid %s <%s> 5' % (ref_name, mu_t.TO.mu_name)
    # assert alloc_str in out
    init_str = '.init %s = {%d 5 {%s}}' % (ref_name, ll_ps.hash, ' '.join(map(lambda c: str(ord(c)), ll_ps.chars)))
    # assert init_str in out
    # assert ".init %s = %s" % (gcell.mu_name, ref_name)


def test_excobj():
    def main(argv):
        return int(argv[0]) * 10

    t, _, g = gengraph(main, [[str]], backendopt=True)

    t.graphs = prepare(t.graphs, g)

    mutyper = MuTyper(t)
    for _g in t.graphs:
        mutyper.specialise(_g)

    hailgen = HAILGenerator()
    for gcell, ldgcell in mutyper.ldgcells.items():
        print gcell, ldgcell
        hailgen.add_gcell(gcell)

    strio = StringIO()
    hailgen.codegen(strio)
    out = strio.getvalue()
    strio.close()
    print out
