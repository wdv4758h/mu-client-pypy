from rpython.mutyper.muts.muops import *
from ..muts.mutype import *


def test_binaryops():
    a = Variable('a')
    b = Variable('b')
    a.mu_name = MuName(a.name)
    b.mu_name = MuName(b.name)
    a.mu_type = int64_t
    b.mu_type = int64_t
    op = ADD([a, b])
    assert op.result.mu_type == int64_t
    assert isinstance(op, MuOperation)
    assert repr(op) == "@rtn_0 = ADD <@i64> @a_0 @b_0 "
