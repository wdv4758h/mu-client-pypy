from StringIO import StringIO

from rpython.mutyper.mutyper import MuTyper
from ..genmu import MuTextIRGenerator
from rpython.rtyper.test.test_llinterp import gengraph
from ..preps import prepare


def test_genmu():
    def main(argv):
        return int(argv[0]) * 10

    t, _, g = gengraph(main, [[str]], backendopt=True)

    t.graphs = prepare(t.graphs, g)

    mutyper = MuTyper()
    for _g in t.graphs:
        mutyper.specialise(_g)

    gen = MuTextIRGenerator(t.graphs, mutyper, g)

    strio_uir = StringIO()
    strio_hail = StringIO()

    gen.codegen(strio_uir, strio_hail)

    uir = strio_uir.getvalue()
    strio_uir.close()
    hail = strio_hail.getvalue()
    strio_hail.close()

    print uir
    print hail
