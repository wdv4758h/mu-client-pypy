from rpython.mutyper.mutyper import MuTyper
from ..genmu import MuTextIRGenerator
from rpython.rtyper.test.test_llinterp import gengraph
from ..preps import prepare


def test_genmu(tmpdir):
    def main(argv):
        return int(argv[0]) * 10

    t, _, g = gengraph(main, [[str]], backendopt=True)

    t.graphs = prepare(t.graphs, g)

    mutyper = MuTyper()
    for _g in t.graphs:
        mutyper.specialise(_g)

    gen = MuTextIRGenerator(t.graphs, mutyper, g)

    fp = open("%s/bundle.uir" % tmpdir, 'w')
    gen.codegen(fp)
    fp.close()

    fp = open("%s/bundle.uir" % tmpdir, 'r')
    code = fp.read()
    print code
