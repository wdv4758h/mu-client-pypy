from rpython.flowspace.model import Variable
from rpython.rtyper.test.test_llinterp import gengraph
from ..exctran import MuExceptionTransformer


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

    # g.view()
    # ------------------------
    # blk_0
    # input: [string_0, a_0, b_0, c_0, d_0]
    # operations:
    # v36 = direct_call(( < * fn
    # f >), string_0)
    # switch: last_exception
    # exits: [('blk_1', [b_0, a_0]), ('blk_3', [last_exc_value_0, d_0, c_0]), ('blk_4', [last_exc_value_1])]
    # ------------------------

    excblk = g.startblock
    norlnk = excblk.exits[0]
    blk3 = excblk.exits[1].target
    blk4 = excblk.exits[2].target
    exctran = MuExceptionTransformer(t)

    exctran.exctran_block(excblk)

    # g.view()
    assert len(excblk.exits) == 2

    assert excblk.exits[0].target is norlnk.target
    assert excblk.exits[0].args is norlnk.args

    assert len(excblk.exits[1].args) == 2
    for arg in excblk.exits[1].args:
        assert arg in excblk.inputargs

    catblk = excblk.exits[1].target
    assert not catblk.inputargs is excblk.exits[1].args
    f = lambda a: a._name[:-1] if isinstance(a, Variable) else a
    assert [f(a) for a in catblk.inputargs] == [f(a) for a in excblk.exits[1].args] # but the names are the same

    assert len(catblk.exits) == 1
    for arg in catblk.exits[0].args[2:]:
        assert arg in catblk.inputargs
    assert catblk.exits[0].args[0]._name[:-1] == "exc_t"
    assert catblk.exits[0].args[1]._name[:-1] == "exc_v"

    cmpblk = catblk.exits[0].target
    assert not cmpblk.inputargs is catblk.exits[0].args
    assert [f(a) for a in cmpblk.inputargs] == [f(a) for a in catblk.exits[0].args]  # but the names are the same

    assert len(cmpblk.operations) == 1
    assert cmpblk.exitswitch is cmpblk.operations[0].result

    assert len(cmpblk.exits) == 2
    assert cmpblk.exits[0].target is blk4   # failed comparison
    assert cmpblk.exits[1].target is blk3   # successful comparison
    for e in cmpblk.exits:
        for arg in e.args:
            assert arg in cmpblk.inputargs
    assert [f(a) for a in cmpblk.exits[0].args] == ["exc_v"]
    inargs = cmpblk.exits[1].target.inputargs
    inargs_names = [f(a) for a in inargs]
    inargs_names[inargs_names.index("last_exc_value")] = "exc_v"
    assert [f(a) for a in cmpblk.exits[1].args] == inargs_names