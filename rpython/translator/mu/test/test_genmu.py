from StringIO import StringIO

from rpython.mutyper.mutyper import MuTyper
from rpython.mutyper.tools.textgraph import print_graph
from rpython.mutyper.tools.search import search_op
from ..genmu import MuTextIRGenerator
from rpython.rtyper.test.test_llinterp import gengraph
from ..preps import prepare


def test_genmu():
    def main(argv):
        print int(argv[0]) * 10
        return 0

    t, _, g = gengraph(main, [[str]], backendopt=True)

    t.graphs = prepare(t.graphs, g)

    mutyper = MuTyper()
    for _g in t.graphs:
        print_graph(_g)
        mutyper.specialise(_g)

    gen = MuTextIRGenerator(t.graphs, mutyper, g)

    strio_uir = StringIO()
    strio_hail = StringIO()
    strio_exfn = StringIO()
    gen.codegen(strio_uir, strio_hail, strio_exfn)

    uir = strio_uir.getvalue()
    strio_uir.close()
    hail = strio_hail.getvalue()
    strio_hail.close()
    exfn = strio_exfn.getvalue()
    strio_exfn.close()

    print uir
    print hail
    print exfn


def test_investigate():
    def main(argv):
        print int(argv[0]) * 10
        return 0

    t, _, g = gengraph(main, [[str]], backendopt=True)

    t.graphs = prepare(t.graphs, g)

    g, blkidx, op = search_op(t.graphs, lambda op: op.opname == 'force_cast').next()

    print_graph(g)
    print "blk_{}".format(blkidx)
    print op
    print "{arg_t} -> {res_t}".format(arg_t=op.args[0].concretetype, res_t=op.result.concretetype)
