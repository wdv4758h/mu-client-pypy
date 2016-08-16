from rpython.flowspace.model import Variable, Constant
from rpython.rtyper.test.test_llinterp import gengraph
from rpython.translator.mu.preps import prepare
from ..exctran import MuExceptionTransformer
from rpython.mutyper.tools.textgraph import print_graph, print_block
from copy import copy


def test_exctran():
    """
    A similar situation as the follwing:
                               +--------+
                               | excblk |
                               +--------+
                                 |  |  |      [last_exception, last_exc_value]
                 +---------------+  |  +--------------------+
                 | [a, b]           |                       |
                 |                  |[c, d, last_exc_value] |
              +--v---+       +------v------+         +------v-------+
              |[a, b]|       |[c, d, exc_v]|         |[exc_t, exc_v]|
              |      |       |             |         |              |
              | blk0 |       |    blk1     |         |     blk2     |
              +------+       +-------------+         +--------------+

                                    ++
                                    ||
                                    ||
                                    ||
                                    ||
                                    ||
                                    ||
                                    ||
                                    vv

                                +--------+
                                | excblk |
                                +--------+
                                  |  |
                  +---------------+  |[c, d]
                  |    [a, b]        |
                  |                  |
               +--v---+       +------v------+
               |[a, b]|       |   [c, d]    |
               |      |       |             |
               | blk0 |       |   catblk    |
               +------+       +-------------+
                                     |
                                     |[exc_t, exc_v, c, d]
                                     |
                                     v
                          +--------------------+
                          |[exc_t, exc_v, c, d]|
                          |       cmpblk       |
                          | cmp_res = call(...)|
                          |                    |
                          |exitswitch: cmp_res |
                          +--------------------+
                               |       |
                    +----------+       +---------+ [exc_t, exc_v]
                    |  [c, d, exc_v]             |
                    |                            |
             +------v------+              +------v-------+
             |[c, d, exc_v]|              |[exc_t, exc_v]|
             |             |              |              |
             |    blk1     |              |     blk2     |
             +-------------+              +--------------+
    @return:
    """
    class MyError(Exception):
        pass
    def f(string):
        try:
            return int(string)
        except Exception:
            raise MyError
    def main(string, a, b, c, d):
        try:
            f(string)
        except MyError as e:
            print "Got MyError: ", e
            return c + d
        except Exception as e:
            print "Got %s" % e.__class__
            return 1
        return a + b
    t, _, g = gengraph(main, [str, int, int, int, int], backendopt=True)

    print_graph(g)

    excblk = g.startblock
    exctran = MuExceptionTransformer(t)

    exctran.exctran_block(excblk)

    print_graph(g)
    # TODO: verify graph using assertions