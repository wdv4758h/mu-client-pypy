"""
Optimise on the pattern:
    %cmp_res = CMPOP %a %b
    %res = SELECT %cmp_res @1_i8 @0_i8
    %con = EQ %res  @1_i8
    BRANCH2 %con %blk1(...) %blk2(...)
by removing the SELECT and EQ instructions.
"""
from rpython.mutyper.muts.muops import MuOperation, BRANCH2


def _has_pattern(blk):
    __mu_cmp_ops = "EQ NE SGE SGT SLE SLT UGE UGT ULE ULT "
    "FFALSE FTRUE FUNO FUEQ FUNE FUGT FUGE FULT FULE "
    "FORD FOEQ FONE FOGT FOGE FOLT FOLE".split(' ')
    try:
        ops = blk.mu_operations
        assert len(ops) >= 4

        last4 = ops[-4:]
        assert last4[0].opname in __mu_cmp_ops

        assert [op.opname for op in last4[1:]] == "SELECT EQ BRANCH2".split(' ')

        op_cmp, op_select, op_eq, op_branch2 = last4
        assert op_cmp.result is op_select.cond
        assert op_select.result is op_eq.op1
        assert op_eq.result is op_branch2.cond

        return True
    except AssertionError:
        return False


def optimise(graphs):
    for g in graphs:
        for blk in g.iterblocks():
            if _has_pattern(blk):
                blk.mu_operations = blk.mu_operations[:-3] + (blk.mu_operations[-1], )
                br2 = blk.mu_operations[-1]
                MuOperation.__init__(br2, blk.mu_operations[-2].result,
                                     br2.ifTrue, br2.ifFalse)
