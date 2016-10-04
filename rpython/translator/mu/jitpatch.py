"""
Patch some JIT relevant stuff
"""


def patch_jit_typeinfo(db, apigen):
    """
    Patch all the mu_tid field of SizeDescrs
    """
    tl = db.translator
    descrs = tl.warmrunnerdesc.codewriter.assembler.descrs


